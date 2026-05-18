import logging
from typing import Optional
import numpy as np

from avlite.c10_perception.c11_perception_model import EgoState
from avlite.c60_common.c63_trajectory_tracker import TrajectoryTracker
from avlite.c30_control.c31_control_model import ControlComand
from avlite.c30_control.c32_control_strategy import ControlStrategy
from avlite.c30_control.c39_settings import ControlSettings

log = logging.getLogger(__name__)

class StanleyController(ControlStrategy):
    def __init__(self, tj:Optional[TrajectoryTracker]=None, k=None, k_soft=None,
                 lookahead=None, heading_lookahead=None, valpha=None, vbeta=None,
                 vgamma=None, slow_down_cte=None, slow_down_heading_cte=None,
                 slow_down_vel_threshold=None):
        """
        Stanley Controller for trajectory following. The controller also slows down the vehicle if steer CTE is > 0.5
        :param tj: Trajectory to follow.
        :param k: Gain for steering control.
        :param k_soft: Softening factor for steering control (at low speed).
        :param lookahead: Lookahead distance for trajectory following.
        :param valpha, vbeta, vgamma: Parameters for velocity control (not used in this implementation).
        :param slow_down_cte: Threshold for slowing down based on steering CTE.
        :param slow_down_vel_threshold: Threshold for slowing down based on steering CTE.
        """
        super().__init__(tj)
        # Resolve settings at construction time. Binding ControlSettings values in
        # the function signature freezes defaults before YAML profiles are loaded.
        self.lookahead = ControlSettings.stanley_lookahead if lookahead is None else lookahead
        configured_heading_lookahead = getattr(ControlSettings, "stanley_heading_lookahead", self.lookahead)
        self.heading_lookahead = configured_heading_lookahead if heading_lookahead is None else heading_lookahead
        self.k = ControlSettings.stanley_k if k is None else k
        self.k_soft = ControlSettings.stanley_k_soft if k_soft is None else k_soft
        self.cte_steer = 0
        self.slow_down_cte = ControlSettings.stanley_slow_down_cte if slow_down_cte is None else slow_down_cte
        self.slow_down_heading_cte = (
            ControlSettings.stanley_slow_down_heading_cte
            if slow_down_heading_cte is None
            else slow_down_heading_cte
        )
        self.slow_down_vel_threshold = (
            ControlSettings.stanley_slow_down_vel_threshold
            if slow_down_vel_threshold is None
            else slow_down_vel_threshold
        )
        
        self.valpha = ControlSettings.stanley_valpha if valpha is None else valpha
        self.vbeta = ControlSettings.stanley_vbeta if vbeta is None else vbeta
        self.vgamma = ControlSettings.stanley_vgamma if vgamma is None else vgamma
        self.cte_v_sum = 0
        self.cte_velocity = 0
        self.previous_cte_velocity = 0  # For D-term calculation
        self.previous_heading = None

    @staticmethod
    def _is_closed_loop(tj: TrajectoryTracker) -> bool:
        return (
            tj.is_initialized
            and len(tj.path_x) > 2
            and np.hypot(tj.path_x[0] - tj.path_x[-1], tj.path_y[0] - tj.path_y[-1]) < 1e-6
        )

    def _heading_at_s(self, tj: TrajectoryTracker, s: float) -> float:
        if not tj or not tj.is_initialized or len(tj.path_s) == 0:
            raise ValueError("TrajectoryTracker not initialized")

        path_s = np.asarray(tj.path_s, dtype=float)
        target_s = float(s)
        start_s = float(path_s[0])
        end_s = float(path_s[-1])
        if end_s > start_s:
            if self._is_closed_loop(tj):
                lap_length = end_s - start_s
                target_s = start_s + ((target_s - start_s) % lap_length)
            else:
                target_s = float(np.clip(target_s, start_s, end_s))

        wp = tj.get_closest_waypoint_frm_sd(target_s, 0.0)
        return float(tj.path_heading[wp])

    def control(self, ego: EgoState, tj: Optional[TrajectoryTracker]=None, control_dt = None) -> ControlComand:
        if tj is not None:
            self.tj = tj
        elif tj is None and self.tj is None:
            log.warning("Trajectory is not provided. Steering and acceleration set to zero. Please provide a trajectory.")
            return ControlComand(steer=0, acceleration=0)

        heading_target_s = None
        target_heading = None

        # to deal with fast replanning, need to have a lookahead to the next trajectory
        if self.tj.parent_trajectory is not None:  
            parent = self.tj.parent_trajectory
            sp, dp =  parent.convert_xy_to_sd(ego.x, ego.y)
            cte_parent_s = sp + self.lookahead
            x, y =  parent.convert_sd_to_xy(cte_parent_s, dp)
            s, cte = self.tj.convert_xy_to_sd(x, y)
            s_, cte_ = self.tj.convert_xy_to_sd(ego.x, ego.y)

            heading_parent_s = sp + self.heading_lookahead
            heading_target_s = heading_parent_s
            target_heading = self._heading_at_s(parent, heading_parent_s)

            log.debug(f"CTE with Lookahead: {self.lookahead}, cte: {cte:.2f}, W.O LA cte: {cte_:.2f}")
            # Also update current_wp for local trajectory to get correct target velocity
            self.tj.update_waypoint_by_xy(ego.x, ego.y)
        else:   
            self.tj.update_waypoint_by_xy(ego.x, ego.y)
            s, cte = self.tj.convert_xy_to_sd(ego.x, ego.y)
            heading_target_s = s + self.heading_lookahead

        self.cte_steer = cte

        ##################################
        # Compute the steering: Stanley
        ##################################
            
        if target_heading is None:
            target_heading = self._heading_at_s(self.tj, heading_target_s)
        current_heading = self.tj.get_current_heading()
        heading_error = normalize_angle(target_heading - ego.theta)
        log.debug(
            f"heading error: {heading_error:+6.2f} "
            f"[target_s: {heading_target_s:+.2f}, target: {target_heading:+6.2f}, "
            f"current: {current_heading:+6.2f}, ego: {ego.theta:+6.2f}]"
        )
        steer1 = heading_error + np.arctan2(self.k * -cte, ego.velocity + self.k_soft)
        log.debug( f"Steer: {steer1:+6.2f} ")
        steer = np.clip(steer1, -ego.max_steering, ego.max_steering)
        # if steer1 !=  steer:
        #     log.warning(f"Steering angle {steer1:+6.2f} clipped to {steer:+6.2f} due to limits [{ego.min_steering:+6.2f}, {ego.max_steering:+6.2f}]. Heading error: {heading_error:+6.2f} ")


        ##################################
        # Compute the velocity control PID
        ##################################
        idx = self.tj.current_wp
        target_velocity = self.tj.velocity[idx]

        prev_cte_v = self.cte_velocity
        self.cte_velocity = ego.velocity - target_velocity
        self.cte_v_sum += self.cte_velocity

        vP = -self.valpha * self.cte_velocity
        vI = -self.vbeta * self.cte_v_sum
        vD = -self.vgamma * (self.cte_velocity - prev_cte_v)  # D-term: rate of change of error

        # Compute the acceleration
        acc = vP + vI + vD
        
        # Emergency braking: if target velocity is 0 (or very low) and we're still moving,
        # apply maximum braking force regardless of PID output
        if target_velocity < 0.5 and ego.velocity > 1.0:
            # Emergency stop requested - apply max deceleration
            emergency_acc = ego.min_acceleration * 0.9  # 90% of max braking
            if acc > emergency_acc:
                log.warning(f"Emergency braking: overriding PID acc {acc:.2f} with {emergency_acc:.2f}")
                acc = emergency_acc
        
        acc = np.clip(acc, ego.min_acceleration, ego.max_acceleration)

        # lower the speed if abs(steer) > 0.5
        if (np.abs(self.cte_steer) > self.slow_down_cte or np.abs(heading_error) > self.slow_down_heading_cte) \
            and ego.velocity > self.slow_down_vel_threshold:
            acc2 = acc - 3 * np.e**np.abs(self.cte_steer)  # reduce acceleration based on steering error
            acc2 = np.clip(acc2, ego.min_acceleration, ego.max_acceleration)
            log.debug(f"Steering error {self.cte_steer:+6.2f} is large, reducing acceleration from {acc:.2f} to {acc2:.2f}")
            acc = acc2

        log.debug(f"Acc  : {acc:+6.2f} [P={vP:+.3f}, I={vI:+.3f}, D={vD:+.3f}] based on CTE: {self.cte_velocity:+.2f} ({ego.velocity:.2f} vs target: {target_velocity:.2f})")

        cmd = ControlComand(steer=steer, acceleration=acc)
        self.cmd = cmd
        return cmd

    def reset(self):
        self.cte_v_sum = 0
        self.cte_velocity = 0
        self.previous_cte_velocity = 0


def normalize_angle(angle):
    """Normalize angle to [-pi, pi] range"""
    return ((angle + np.pi) % (2 * np.pi)) - np.pi
