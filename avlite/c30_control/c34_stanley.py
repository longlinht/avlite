import logging
from typing import Optional

import numpy as np

from avlite.c10_perception.c11_perception_model import EgoState, PerceptionModel
from avlite.c20_planning.c21_planning_model import GlobalPlan, LocalPlan
from avlite.c30_control.c31_control_model import ControlCommand
from avlite.c30_control.c32_control_strategy import ControlStrategy
from avlite.c30_control.c39_settings import ControlSettings, ControlSettingsSchema
from avlite.c50_common.c52_world_sensor_datatypes import SensorFrame
from avlite.c50_common.c54_trajectory_tracker import TrajectoryTracker

log = logging.getLogger(__name__)


class StanleyController(ControlStrategy):
    """Stanley lateral control with PID reference-speed tracking."""

    def __init__(
        self,
        tj: Optional[TrajectoryTracker] = None,
        k=None,
        k_soft=None,
        lookahead=None,
        heading_lookahead=None,
        valpha=None,
        vbeta=None,
        vgamma=None,
        v_integral_accel_limit=None,
        slow_down_cte=None,
        slow_down_heading_cte=None,
        slow_down_vel_threshold=None,
        setting: ControlSettingsSchema | None = None,
    ):
        # AVLite 0.5 briefly accepted ``setting`` as the second positional
        # argument. Detect that form while retaining the older gain overrides.
        if setting is None and k is not None and hasattr(k, "c34_stanley_k"):
            setting, k = k, None
        setting = setting or ControlSettings
        super().__init__(tj)
        self.setting = setting
        self.lookahead = (
            setting.c34_stanley_lookahead if lookahead is None else lookahead
        )
        configured_heading_lookahead = getattr(
            setting, "c34_stanley_heading_lookahead", self.lookahead
        )
        self.heading_lookahead = (
            configured_heading_lookahead
            if heading_lookahead is None
            else heading_lookahead
        )
        self.k = setting.c34_stanley_k if k is None else k
        self.k_soft = setting.c34_stanley_k_soft if k_soft is None else k_soft
        self.slow_down_cte = (
            setting.c34_stanley_slow_down_cte
            if slow_down_cte is None
            else slow_down_cte
        )
        self.slow_down_heading_cte = (
            setting.c34_stanley_slow_down_heading_cte
            if slow_down_heading_cte is None
            else slow_down_heading_cte
        )
        self.slow_down_vel_threshold = (
            setting.c34_stanley_slow_down_vel_threshold
            if slow_down_vel_threshold is None
            else slow_down_vel_threshold
        )
        self.valpha = setting.c34_stanley_valpha if valpha is None else valpha
        self.vbeta = setting.c34_stanley_vbeta if vbeta is None else vbeta
        self.vgamma = setting.c34_stanley_vgamma if vgamma is None else vgamma
        configured_integral_limit = getattr(
            setting, "c34_stanley_v_integral_accel_limit", 2.0
        )
        self.v_integral_accel_limit = (
            configured_integral_limit
            if v_integral_accel_limit is None
            else v_integral_accel_limit
        )
        self.cte_steer = 0.0
        self.cte_v_sum = 0.0
        self.cte_velocity = 0.0
        self.previous_cte_velocity = 0.0

    @staticmethod
    def _is_closed_loop(tj: TrajectoryTracker) -> bool:
        return (
            tj.is_initialized
            and len(tj.path_x) > 2
            and np.hypot(
                tj.path_x[0] - tj.path_x[-1],
                tj.path_y[0] - tj.path_y[-1],
            )
            < 1e-6
        )

    def _heading_at_s(self, tj: TrajectoryTracker, s: float) -> float:
        if not tj.is_initialized or len(tj.path_s) == 0:
            raise ValueError("TrajectoryTracker not initialized")

        path_s = np.asarray(tj.path_s, dtype=float)
        target_s = float(s)
        start_s = float(path_s[0])
        end_s = float(path_s[-1])
        if end_s > start_s:
            if self._is_closed_loop(tj):
                target_s = start_s + ((target_s - start_s) % (end_s - start_s))
            else:
                target_s = float(np.clip(target_s, start_s, end_s))
        wp = tj.get_closest_waypoint_frm_sd(target_s, 0.0)
        return float(tj.path_heading[wp])

    def control(
        self,
        ego: EgoState,
        plan: GlobalPlan | LocalPlan | TrajectoryTracker | None = None,
        control_dt: float | None = None,
        perception_model: PerceptionModel | None = None,
        sensors: SensorFrame | None = None,
    ) -> ControlCommand:
        del control_dt, perception_model, sensors
        if isinstance(plan, TrajectoryTracker):
            self.tj = plan
        elif plan is not None:
            self.tj = plan.as_trajectory()
        elif self.tj is None:
            log.warning("Trajectory is not provided; returning a zero control command.")
            return ControlCommand(steer=0.0, acceleration=0.0)

        target_heading = None
        heading_target_s = 0.0
        if self.tj.parent_trajectory is not None:
            parent = self.tj.parent_trajectory
            parent_s, parent_d = parent.convert_xy_to_sd(ego.x, ego.y)
            cte_x, cte_y = parent.convert_sd_to_xy(
                parent_s + self.lookahead, parent_d
            )
            _, cte = self.tj.convert_xy_to_sd(cte_x, cte_y)
            self.tj.update_waypoint_by_xy(ego.x, ego.y)
            heading_target_s = parent_s + self.heading_lookahead
            target_heading = self._heading_at_s(parent, heading_target_s)
        else:
            self.tj.update_waypoint_by_xy(ego.x, ego.y)
            current_s, cte = self.tj.convert_xy_to_sd(ego.x, ego.y)
            heading_target_s = current_s + self.heading_lookahead

        self.cte_steer = cte
        if target_heading is None:
            target_heading = self._heading_at_s(self.tj, heading_target_s)
        heading_error = normalize_angle(target_heading - ego.theta)
        raw_steer = heading_error + np.arctan2(
            self.k * -cte, ego.velocity + self.k_soft
        )
        steer = float(
            np.clip(raw_steer, self.ego_min_steering, self.ego_max_steering)
        )

        target_velocity = self.tj.velocity[self.tj.current_wp]
        previous_error = self.cte_velocity
        self.cte_velocity = ego.velocity - target_velocity
        if (
            previous_error != 0.0
            and self.cte_velocity != 0.0
            and np.sign(previous_error) != np.sign(self.cte_velocity)
        ):
            self.cte_v_sum = 0.0
        self.cte_v_sum += self.cte_velocity
        if self.vbeta != 0.0 and self.v_integral_accel_limit is not None:
            integral_limit = abs(float(self.v_integral_accel_limit))
            if integral_limit > 0.0:
                sum_limit = integral_limit / abs(float(self.vbeta))
                self.cte_v_sum = float(
                    np.clip(self.cte_v_sum, -sum_limit, sum_limit)
                )

        v_p = -self.valpha * self.cte_velocity
        v_i = -self.vbeta * self.cte_v_sum
        v_d = -self.vgamma * (self.cte_velocity - previous_error)
        acceleration = v_p + v_i + v_d

        if (
            target_velocity < self.setting.c30_emergency_velocity_threshold
            and ego.velocity > self.setting.c30_emergency_min_moving_velocity
        ):
            emergency_acceleration = (
                self.ego_min_acceleration
                * self.setting.c30_emergency_braking_factor
            )
            acceleration = min(acceleration, emergency_acceleration)

        acceleration = float(
            np.clip(
                acceleration,
                self.ego_min_acceleration,
                self.ego_max_acceleration,
            )
        )
        if ego.velocity <= 0.0 and self.cte_v_sum > 0.0:
            self.cte_v_sum = 0.0
        if ego.velocity <= 0.0 and acceleration < 0.0:
            acceleration = 0.0

        tracking_error_is_large = (
            abs(self.cte_steer) > self.slow_down_cte
            or abs(heading_error) > self.slow_down_heading_cte
        )
        if tracking_error_is_large and ego.velocity > self.slow_down_vel_threshold:
            if self.cte_velocity > 0.0:
                bounded_cte = float(np.clip(abs(self.cte_steer), 0.0, 20.0))
                acceleration -= 3.0 * np.exp(bounded_cte)
            else:
                speed_deficit = max(0.0, target_velocity - ego.velocity)
                acceleration = (
                    min(acceleration, speed_deficit)
                    if acceleration > 0.0
                    else max(0.0, acceleration)
                )
            acceleration = float(
                np.clip(
                    acceleration,
                    self.ego_min_acceleration,
                    self.ego_max_acceleration,
                )
            )

        cmd = ControlCommand(steer=steer, acceleration=acceleration)
        self.cmd = cmd
        return cmd

    def reset(self):
        self.cte_v_sum = 0.0
        self.cte_velocity = 0.0
        self.previous_cte_velocity = 0.0


def normalize_angle(angle):
    """Normalize angle to the [-pi, pi] range."""
    return ((angle + np.pi) % (2 * np.pi)) - np.pi
