"""Compatibility factory for pre-0.5 plugins.

The current application factory lives in :mod:`avlite.c60_apps`.  Core code
must not depend on that application layer, so this module assembles the legacy
stack directly from the core strategy registries.
"""

from __future__ import annotations

import inspect
import logging

from avlite.c10_perception.c11_perception_model import EGO_AGENT_ID, EgoState, Map, PerceptionModel
from avlite.c10_perception.c12_perception_strategy import PerceptionStrategy
from avlite.c10_perception.c13_localization_strategy import LocalizationStrategy
from avlite.c20_planning.c21_planning_model import GlobalPlan
from avlite.c20_planning.c22_global_planning_strategy import GlobalPlannerStrategy
from avlite.c20_planning.c23_local_planning_strategy import LocalPlanningStrategy
from avlite.c20_planning.c28_local_lattice_planners import GreedyLatticePlanner  # noqa: F401
from avlite.c30_control.c32_control_strategy import ControlStrategy
from avlite.c30_control.c33_pid import PIDController  # noqa: F401
from avlite.c30_control.c34_stanley import StanleyController  # noqa: F401
from avlite.c30_control.c35_pure_pursuit import PurePursuitController  # noqa: F401
from avlite.c40_execution.c41_world_bridge import WorldBridge
from avlite.c40_execution.c42_execution_strategy import ExecutionStrategy
from avlite.c40_execution.c44_sync_executer import SyncExecuter  # noqa: F401
from avlite.c40_execution.c45_async_threaded_executer import AsyncThreadedExecuter  # noqa: F401
from avlite.c40_execution.c46_basic_sim import BasicSim  # noqa: F401
from avlite.c40_execution.c49_settings import ExecutionSettings
from avlite.c50_common.c51_capabilities import StackCapability
from avlite.c60_apps.c68_paths import DataPaths


log = logging.getLogger(__name__)


class RaceGlobalPlanner(GlobalPlannerStrategy):
    """Expose an already-loaded race trajectory through the legacy class name."""

    stack_requirements = frozenset()
    stack_capabilities = frozenset({StackCapability.GLOBAL_PLAN})

    def plan(self, perception_model=None, sensors=None) -> GlobalPlan:
        del perception_model, sensors
        return self.global_plan


def _registered(name: str, registry: dict, label: str):
    try:
        return registry[name]
    except KeyError as exc:
        raise ValueError(f"Could not load {label} {name!r}: not registered") from exc


def _supported_kwargs(cls, **kwargs) -> dict:
    parameters = inspect.signature(cls.__init__).parameters
    if any(param.kind is inspect.Parameter.VAR_KEYWORD for param in parameters.values()):
        return kwargs
    return {name: value for name, value in kwargs.items() if name in parameters}


def _load_legacy_extensions() -> None:
    """Load legacy extensions without coupling the core to the current app factory."""
    from avlite.c60_common.c61_setting_utils import import_all_modules

    import_all_modules()
    configured = {
        **ExecutionSettings.community_extensions,
        **ExecutionSettings.community_plugins,
    }
    for name, path in configured.items():
        log.info("Loading legacy extension %s from %s", name, path)
        import_all_modules(path, pkg_name=name)


def executor_factory(
    executer_type=ExecutionSettings.executer_type,
    bridge=ExecutionSettings.bridge,
    perception_strategy_name=ExecutionSettings.perception,
    localization_strategy_name=ExecutionSettings.localization,
    global_planner_strategy_name=ExecutionSettings.global_planner,
    local_planner_strategy_name=ExecutionSettings.local_planner,
    controller_strategy_name=ExecutionSettings.controller,
    perception_dt=ExecutionSettings.perception_dt,
    localization_dt=ExecutionSettings.localization_dt,
    replan_dt=ExecutionSettings.replan_dt,
    control_dt=ExecutionSettings.control_dt,
    default_global_trajectory_file=ExecutionSettings.global_trajectory,
    hd_map=ExecutionSettings.hd_map,
    load_extensions=True,
) -> ExecutionStrategy:
    """Build a stack using the pre-0.5 factory signature."""
    if load_extensions:
        _load_legacy_extensions()

    plan_path = DataPaths.resolve_stored(default_global_trajectory_file)
    global_plan = GlobalPlan.from_file(plan_path)
    stack_ego = EgoState(x=global_plan.start_point[0], y=global_plan.start_point[1])
    stack_ego.agent_id = EGO_AGENT_ID
    perception_model = PerceptionModel(ego_vehicle=stack_ego)

    loaded_map = Map.open(DataPaths.resolve_stored(hd_map)) if hd_map else None
    if loaded_map is not None:
        perception_model.map = loaded_map

    planner_cls = _registered(
        global_planner_strategy_name,
        GlobalPlannerStrategy.registry,
        "global planner",
    )
    global_planner = planner_cls(
        **_supported_kwargs(planner_cls, map=loaded_map)
    )
    global_planner.global_plan = global_plan

    perception = None
    if perception_strategy_name:
        perception_cls = _registered(
            perception_strategy_name,
            PerceptionStrategy.registry,
            "perception strategy",
        )
        perception = perception_cls(perception_model=perception_model)

    localization = None
    if localization_strategy_name:
        localization_cls = _registered(
            localization_strategy_name,
            LocalizationStrategy.registry,
            "localization strategy",
        )
        localization = localization_cls(perception_model=perception_model)

    local_planner = None
    if local_planner_strategy_name:
        local_planner_cls = _registered(
            local_planner_strategy_name,
            LocalPlanningStrategy.registry,
            "local planner",
        )
        local_planner = local_planner_cls(
            **_supported_kwargs(
                local_planner_cls,
                global_plan=global_plan,
                env=perception_model,
                pm=perception_model,
            )
        )

    controller = None
    if controller_strategy_name:
        controller_cls = _registered(
            controller_strategy_name,
            ControlStrategy.registry,
            "controller",
        )
        controller = controller_cls()
        if global_plan.trajectory is not None:
            controller.set_trajectory_tracker(global_plan.trajectory)

    world_ego = EgoState(
        x=stack_ego.x,
        y=stack_ego.y,
        theta=stack_ego.theta,
        velocity=stack_ego.velocity,
    )
    world_ego.agent_id = EGO_AGENT_ID
    world_model = PerceptionModel(ego_vehicle=world_ego)
    reference_point = ExecutionSettings.c40_reference_point
    world_kwargs = {
        "ego_state": world_ego,
        "pm": world_model,
        "perception_model": world_model,
        "reference_point": (
            tuple(float(value) for value in reference_point[:2])
            if reference_point and len(reference_point) >= 2
            else None
        ),
        "map": loaded_map,
    }
    try:
        world_cls = _registered(bridge, WorldBridge.registry, "world bridge")
        world = world_cls(**_supported_kwargs(world_cls, **world_kwargs))
    except Exception as exc:
        log.error(
            "Error loading world bridge %s: %s; using BasicSim fallback",
            bridge,
            exc,
        )
        world = BasicSim(**_supported_kwargs(BasicSim, **world_kwargs))

    executer_cls = _registered(executer_type, ExecutionStrategy.registry, "executer")
    executer = executer_cls(
        **_supported_kwargs(
            executer_cls,
            perception_model=perception_model,
            perception=perception,
            global_planner=global_planner,
            local_planner=local_planner,
            controller=controller,
            world=world,
            localization=localization,
            mapping=None,
            perception_dt=perception_dt,
            localization_dt=localization_dt,
            replan_dt=replan_dt,
            control_dt=control_dt,
            tasks=[],
        )
    )
    executer._requested_executer_type = executer_type
    return executer


__all__ = ["RaceGlobalPlanner", "executor_factory"]
