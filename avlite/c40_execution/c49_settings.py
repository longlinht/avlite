from typing import ClassVar

from pydantic import Field

from avlite.c60_apps.c64_settings_schema import SettingsSchema


class ExecutionSettingsSchema(SettingsSchema):
    filepath: ClassVar[str] = "configs/c40_execution.yaml"

    c40_executer_type: str = Field(default="SyncExecuter", description="Executer class name.")
    c40_bridge: str = Field(default="BasicSim", description="World bridge class name.")
    c40_perception: str = Field(default="", description="Perception strategy class; empty omits the module.")
    c40_localization: str = Field(default="", description="Localization strategy class; empty omits the module.")
    c40_mapping: str = Field(default="MapReader", description="Mapping strategy class; empty omits the module.")
    c40_global_planner: str = Field(default="GlobalCenterlineRacePlanner", description="Global planner class name.")
    c40_local_planner: str = Field(default="GreedyLatticePlanner", description="Local planner class name.")
    c40_controller: str = Field(default="StanleyController", description="Controller class name.")
    c40_execution_tasks: list[str] = Field(
        default_factory=list,
        description="TaskStrategy class names appended after each stack tick.",
    )
    c40_perception_dt: float = Field(default=0.01, ge=0.001, description="Perception tick period (s).")
    c40_localization_dt: float = Field(default=0.01, ge=0.001, description="Localization tick period (s).")
    c40_replan_dt: float = Field(default=0.01, ge=0.001, description="Planning tick period (s).")
    c40_control_dt: float = Field(default=0.01, ge=0.001, description="Control tick period (s).")
    c40_sim_dt: float = Field(default=0.01, ge=0.001, description="Simulation integration period (s).")
    c40_pace_perception: bool = Field(default=True, description="Pace perception to its configured period.")
    c40_pace_replan: bool = Field(default=True, description="Pace planning to its configured period.")
    c40_pace_control: bool = Field(default=True, description="Pace control to its configured period.")
    c40_pace_sim: bool = Field(default=True, description="Use a fixed simulation integration period.")
    c40_global_trajectory: str = Field(
        default="data/yas_marina_real_race_line_mue_0_5_3_m_margin.json",
        description="Default global plan JSON path.",
    )
    c40_map: str = Field(
        default="data/race_boundary_yas_marina.map.json",
        description="Map path; empty omits the map.",
    )
    c40_reference_point: list[float] | None = Field(
        default_factory=lambda: [24.46992202098782, 54.60522506805341],
        description="WGS84 map origin [latitude, longitude].",
    )
    c40_start_pose: list[float] | None = Field(
        default=None,
        description="Ego start pose [x, y, theta]; null uses the plan start.",
    )
    c40_async_combined_perception_planning: bool = Field(
        default=True,
        description="Run perception and planning concurrently.",
    )
    c40_log_level: str = Field(default="INFO", description="Python logging level.")
    c40_log_to_file: bool = Field(default=False, description="Write logs to file.")

    c41_world_capabilities: list[str] | None = Field(
        default=None,
        description="Enabled WorldCapability names; null enables all advertised capabilities.",
    )
    c41_world_stack_capabilities: list[str] | None = Field(
        default=None,
        description="Enabled ground-truth StackCapability names; null enables all advertised capabilities.",
    )

    c46_npc_speed_factor: float = Field(default=0.8, description="NPC speed as a fraction of plan speed.")
    c46_npc_control: bool = Field(default=True, description="Enable NPC vehicle controllers in BasicSim.")
    c46_lidar_range: float = Field(default=50.0, description="Simulated LiDAR range (m).")
    c46_lidar_num_beams: int = Field(default=360, description="Number of simulated LiDAR beams.")
    c46_lidar_fov_deg: float = Field(default=360.0, description="Simulated LiDAR field of view (degrees).")


def _legacy_alias(target: str) -> property:
    """Expose pre-0.5 setting names while keeping one canonical value."""

    def get_value(self):
        return getattr(self, target)

    def set_value(self, value):
        setattr(self, target, value)

    return property(get_value, set_value)


_LEGACY_ALIASES = {
    "executer_type": "c40_executer_type",
    "bridge": "c40_bridge",
    "perception": "c40_perception",
    "localization": "c40_localization",
    "mapping": "c40_mapping",
    "global_planner": "c40_global_planner",
    "local_planner": "c40_local_planner",
    "controller": "c40_controller",
    "perception_dt": "c40_perception_dt",
    "localization_dt": "c40_localization_dt",
    "replan_dt": "c40_replan_dt",
    "control_dt": "c40_control_dt",
    "sim_dt": "c40_sim_dt",
    "hd_map": "c40_map",
    "log_level": "c40_log_level",
    "log_to_file": "c40_log_to_file",
    "basic_sim_default_trajectory": "c40_global_trajectory",
    "basic_sim_npc_speed_factor": "c46_npc_speed_factor",
    "basic_sim_npc_control": "c46_npc_control",
}
for _legacy_name, _canonical_name in _LEGACY_ALIASES.items():
    setattr(ExecutionSettingsSchema, _legacy_name, _legacy_alias(_canonical_name))


def _legacy_global_trajectory() -> property:
    def get_value(self):
        value = self.c40_global_trajectory
        prefix = "avlite/data/"
        return value[len("avlite/") :] if value.startswith(prefix) else value

    def set_value(self, value):
        self.c40_global_trajectory = value

    return property(get_value, set_value)


ExecutionSettingsSchema.global_trajectory = _legacy_global_trajectory()

_LEGACY_VALUES = {
    "community_extensions": {},
    "community_plugins": {},
    "default_extensions": [],
    "provide_ground_truth": False,
    "provide_rgb": False,
    "provide_lidar": False,
}


def _legacy_value(name: str) -> property:
    def get_value(self):
        return _LEGACY_VALUES[name]

    def set_value(self, value):
        _LEGACY_VALUES[name] = value

    return property(get_value, set_value)


for _legacy_name in _LEGACY_VALUES:
    setattr(ExecutionSettingsSchema, _legacy_name, _legacy_value(_legacy_name))


# Singleton instance: mutated in place by profile loaders; never rebind.
ExecutionSettings = ExecutionSettingsSchema()
