import logging
import time

from avlite.c20_planning.c21_planning_model import GlobalPlan
from avlite.c20_planning.c28_trajectory import Trajectory, convert_sd_path_to_xy_path
from avlite.c10_perception.c11_perception_model import PerceptionModel, EgoState, AgentState
from avlite.c10_perception.c12_perception_strategy import PerceptionStrategy
from avlite.c10_perception.c13_localization_strategy import LocalizationStrategy
from avlite.c20_planning.c22_global_planning_strategy import GlobalPlannerStrategy
from avlite.c20_planning.c23_local_planning_strategy import LocalPlannerStrategy
from avlite.c30_control.c32_control_strategy import ControlStrategy
from avlite.c40_execution.c49_settings import ExecutionSettings
from avlite.c40_execution.c41_execution_model import Executer
from avlite.c40_execution.c41_execution_model import WorldBridge
from avlite.c60_common.c62_capabilities import WorldCapability, PerceptionCapability

log = logging.getLogger(__name__)

class SyncExecuter(Executer):
    def __init__(
        self,
        perception_model: PerceptionModel,
        perception: PerceptionStrategy = None,
        global_planner: GlobalPlannerStrategy = None,
        local_planner: LocalPlannerStrategy = None,
        controller: ControlStrategy = None,
        world: WorldBridge = None,
        localization: LocalizationStrategy = None,
        perception_dt=ExecutionSettings.perception_dt,
        replan_dt=ExecutionSettings.replan_dt,
        control_dt=ExecutionSettings.control_dt,
        localization_dt=ExecutionSettings.localization_dt,
    ):
        """
        Initializes the SyncExecuter with the given perception model, global planner, local planner, control strategy, and world interface.
        """
        super().__init__(perception_model,perception, global_planner, local_planner, controller, world,
                         localization=localization, perception_dt=perception_dt, replan_dt=replan_dt,
                         control_dt=control_dt, localization_dt=localization_dt)

        self.elapsed_real_time = 0
        self.elapsed_sim_time = 0

        self.__prev_exec_time = None
        self.__perception_last_time = 0.0
        self.__planner_last_time = 0.0
        self.__controller_last_time = 0.0
        self.__localization_last_time = 0.0
        self._global_plan_mismatch_warned = False
        self._fallback_global_plan_set = False


    def step(self, perception_dt = 0.01,  control_dt=0.01, replan_dt=0.01, localization_dt=0.01, sim_dt=0.01, call_replan=True, call_control=True, call_perceive=True, call_localize=True,) -> None:
        """ Executes a single step of the simulation, including planning, control, and perception. """

        pln_time_txt, cn_time_txt, pr_time_txt, loc_time_txt, sim_time_txt = "", "", "", "", ""
        t0 = time.time()

        self.ego_state = self.world.get_ego_state()
        # Safety guard: if global plan start is far from current ego, set fallback plan once.
        try:
            start = self.local_planner.global_plan.start_point
            dist = ((self.ego_state.x - start[0]) ** 2 + (self.ego_state.y - start[1]) ** 2) ** 0.5
            if dist > 50.0:
                if not self._global_plan_mismatch_warned:
                    log.warning(
                        f"Global plan start is far from ego (dist={dist:.1f}m). "
                        "Using straight-line fallback plan from current pose."
                    )
                    self._global_plan_mismatch_warned = True
                if not self._fallback_global_plan_set:
                    n_points = 20
                    step = 2.0
                    heading = self.ego_state.theta
                    path = [
                        (
                            self.ego_state.x + i * step * math.cos(heading),
                            self.ego_state.y + i * step * math.sin(heading),
                        )
                        for i in range(n_points)
                    ]
                    velocity = [5.0] * n_points
                    traj = Trajectory(path=path, velocity=velocity)
                    left_d = [2.0] * n_points
                    right_d = [-2.0] * n_points
                    left_x, left_y = convert_sd_path_to_xy_path(traj, traj.path_s, left_d)
                    right_x, right_y = convert_sd_path_to_xy_path(traj, traj.path_s, right_d)
                    fallback = GlobalPlan(
                        start_point=path[0],
                        goal_point=path[-1],
                        path=path,
                        velocity=velocity,
                        left_boundary_d=left_d,
                        right_boundary_d=right_d,
                        left_boundary_x=left_x,
                        left_boundary_y=left_y,
                        right_boundary_x=right_x,
                        right_boundary_y=right_y,
                        trajectory=traj,
                    )
                    self.local_planner.set_global_plan(fallback)
                    self._fallback_global_plan_set = True
                # Continue with control using fallback plan.
        except Exception:
            pass

        if call_replan:
            dt_p = self.elapsed_sim_time - self.__planner_last_time
            if dt_p >= replan_dt:
                self.local_planner.replan()
                self.__planner_last_time = self.elapsed_sim_time
                self.planner_fps = 1.0 / dt_p
                pln_time_txt = f" P: {(time.time() - t0):.2} sec,"
                # log.info(f"DT Planner: {dt_p:.4f} sec")

        self.local_planner.step(self.ego_state)

        t1 = time.time()
        if call_control:
            dt_c = self.elapsed_sim_time - self.__controller_last_time
            if dt_c >= control_dt:
                self.__controller_last_time = self.elapsed_sim_time
                self.control_fps = 1.0 / dt_c
                local_tj = self.local_planner.get_local_plan()
                cmd = self.controller.control(self.ego_state, local_tj, control_dt=sim_dt)
                cn_time_txt = f"C: {(time.time() - t1):.4f} sec,"

                self.world.control_ego_state(cmd, dt=sim_dt)
        self.elapsed_sim_time += control_dt
        
        # ---- Localization step ----
        t_loc = time.time()
        if call_localize and self.localization:
            if self.localization.requirements.issubset(self.world.capabilities):
                dt_loc = self.elapsed_sim_time - self.__localization_last_time
                if dt_loc >= localization_dt:
                    self.__localization_last_time = self.elapsed_sim_time
                    self.localization.localize(
                        lidar=self.world.get_lidar_data() if ExecutionSettings.provide_lidar else None,
                        rgb_img=self.world.get_rgb_image() if ExecutionSettings.provide_rgb else None,
                    )
                    self.localization_fps = 1.0 / dt_loc
                    loc_time_txt = f" LOC: {(time.time() - t_loc):.4f} sec,"
            else:
                log.error(f"Localization strategy {self.localization.__class__.__name__} requirements {self.localization.requirements} not satisfied by capabilities: {self.world.capabilities}. Skipping localization step.")

        t2 = time.time()
        if call_perceive:
            if not self.perception:
                log.error("Perception strategy is not set. Skipping perception step.")

            # elif self.perception.supports_detection == False and self.world.supports_ground_truth_detection:
            elif self.perception.requirements.issubset(self.world.capabilities): 
                # log.warning(f"[Executer] Perception step started at {t2:.4f} sec")
                if ExecutionSettings.provide_ground_truth:
                    self.pm = self.world.get_ground_truth_perception_model()
                else:
                    self.pm.agent_vehicles = []
                perception_output = self.perception.perceive(
                    perception_model=self.pm,
                    rgb_img=self.world.get_rgb_image() if ExecutionSettings.provide_rgb else None,
                    depth_img=self.world.get_depth_image(),
                    lidar_data=self.world.get_lidar_data() if ExecutionSettings.provide_lidar else None,
                )

                # log.debug(f"[Executer] Perception output: {perception_output.shape if not isinstance(perception_output, list) else len(perception_output)}")
                log.debug(f"type of perception_output: {type(perception_output)}")
                # log.warning(f"occupancy grid: {self.pm.occupancy_flow}")
                log.debug(f"occupancy grid sizes: {self.pm.grid_bounds}")

            else:
                log.error(f"Perception strategy {self.perception.__class__.__name__} requirements {self.perception.requirements} not satisfied by capabilities: {self.world.capabilities}. Skipping perception step.")

            pr_time_txt = f" PR: {(time.time() - t2):.4f} sec,"



        delta_t_exec = time.time() - self.__prev_exec_time if self.__prev_exec_time is not None else 0
        self.__prev_exec_time = time.time()
        self.elapsed_real_time += delta_t_exec

        log.debug(f"Real Step time: {delta_t_exec:.4f} sec | {pln_time_txt} {cn_time_txt} {loc_time_txt} {pr_time_txt} {sim_time_txt}")
        log.debug( f"Elapsed Real Time: {self.elapsed_real_time:.3f} sec | Elapsed Sim Time: {self.elapsed_sim_time:.3f} sec")


    def run(self, replan_dt=0.5, control_dt=0.01, call_replan=True, call_control=True, call_perceive=False):
        self.reset()
        while True:
            self.step(
                control_dt=control_dt,
                replan_dt=replan_dt,
                call_replan=call_replan,
                call_control=call_control,
                call_perceive=call_perceive,
            )
            time.sleep(control_dt)

    def stop(self):
        pass

    def reset(self):
        super().reset()
        self.__prev_exec_time = None
        self.__time_since_last_replan = 0
