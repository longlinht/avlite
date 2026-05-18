from typing import Optional
from dataclasses import dataclass, field
import logging
import json
import math

from avlite.c10_perception.c18_hdmap import HDMap
from avlite.c60_common.c61_setting_utils import resolve_project_path
from avlite.c60_common.c63_trajectory_tracker import TrajectoryTracker, convert_sd_path_to_xy_path

log = logging.getLogger(__name__)


def _match_opposite_boundary_points(
    source_points: list[tuple[float, float]],
    opposite_points: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    if not source_points or not opposite_points:
        return []

    n_source = len(source_points)
    n_opposite = len(opposite_points)
    search_window = min(n_opposite - 1, max(20, int(round(n_opposite * 0.04))))
    matched_points = []
    for i, source in enumerate(source_points):
        nominal_j = int(round(i * n_opposite / n_source)) % n_opposite
        best_j = nominal_j
        best_dist_sq = math.inf
        for offset in range(-search_window, search_window + 1):
            j = (nominal_j + offset) % n_opposite
            opposite = opposite_points[j]
            dist_sq = (opposite[0] - source[0]) ** 2 + (opposite[1] - source[1]) ** 2
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_j = j
        matched_points.append(opposite_points[best_j])
    return matched_points


@dataclass
class GlobalPlan:
    start_point: tuple[float, float] = (0.0, 0.0)
    goal_point: tuple[float, float] = (0.0, 0.0)
    path: list[tuple[float, float]] = field(default_factory=list)
    velocity: list[float] = field(default_factory=list)
    left_boundary_d: list[float] = field(default_factory=list)
    left_boundary_x: list[float] = field(default_factory=list)
    left_boundary_y: list[float] = field(default_factory=list)
    right_boundary_d: list[float] = field(default_factory=list)
    right_boundary_x: list[float] = field(default_factory=list)
    right_boundary_y: list[float] = field(default_factory=list)
    
    lane_left_boundary_d: list[float] = field(default_factory=list)
    lane_left_boundary_x: list[float] = field(default_factory=list)
    lane_left_boundary_y: list[float] = field(default_factory=list)
    lane_right_boundary_d: list[float] = field(default_factory=list)
    lane_right_boundary_x: list[float] = field(default_factory=list)
    lane_right_boundary_y: list[float] = field(default_factory=list)

    race_mode: bool = True
    trajectory: TrajectoryTracker = field(default_factory=lambda: TrajectoryTracker(path=[], velocity=[]))

    # Optional HDMap and lane path for global planning
    hdmap: Optional[HDMap] = None  
    lane_path: Optional[list[HDMap.Lane]] = None
    
    @classmethod
    def from_file(cls, path_to_track: str) -> "GlobalPlan":
        track_path = resolve_project_path(path_to_track)
        with track_path.open("r") as f:
            data = json.load(f)
            if "ReferenceLine" not in data and "LeftBound" in data and "RightBound" in data:
                left_points = [point[:2] for point in data["LeftBound"]]
                right_points = [point[:2] for point in data["RightBound"]]
                matched_right_points = _match_opposite_boundary_points(left_points, right_points)
                path = [
                    ((left[0] + right[0]) / 2.0, (left[1] + right[1]) / 2.0)
                    for left, right in zip(left_points, matched_right_points)
                ]
                velocity = data.get("ReferenceSpeed") or [4.0] * len(path)
                if len(velocity) != len(path):
                    velocity = [4.0] * len(path)
                trajectory = TrajectoryTracker(path=path, velocity=velocity)
                left_boundary_d = [
                    math.hypot(left[0] - center[0], left[1] - center[1])
                    for left, center in zip(left_points, path)
                ]
                right_boundary_d = [
                    -math.hypot(right[0] - center[0], right[1] - center[1])
                    for right, center in zip(matched_right_points, path)
                ]
                return cls(
                    start_point=path[0],
                    goal_point=path[-1],
                    path=path,
                    velocity=velocity,
                    left_boundary_d=left_boundary_d,
                    right_boundary_d=right_boundary_d,
                    trajectory=trajectory,
                    left_boundary_x=[point[0] for point in left_points],
                    left_boundary_y=[point[1] for point in left_points],
                    right_boundary_x=[point[0] for point in matched_right_points],
                    right_boundary_y=[point[1] for point in matched_right_points],
                )
            path = [point[:2] for point in data["ReferenceLine"]]
            velocity=data["ReferenceSpeed"]
            left_boundary_d=data["LeftBound"]
            right_boundary_d=data["RightBound"]
            trajectory = TrajectoryTracker(path=path, velocity=velocity)
            left_boundary_x, left_boundary_y = convert_sd_path_to_xy_path(trajectory, trajectory.path_s, left_boundary_d)
            right_boundary_x, right_boundary_y = convert_sd_path_to_xy_path(trajectory, trajectory.path_s, right_boundary_d)
            return cls(
                start_point= path[0],
                goal_point=path[-1],
                path=path,
                velocity=velocity,
                left_boundary_d=left_boundary_d,
                right_boundary_d=right_boundary_d,
                trajectory=trajectory,
                left_boundary_x=left_boundary_x,
                left_boundary_y=left_boundary_y,
                right_boundary_x=right_boundary_x,
                right_boundary_y=right_boundary_y,
            )

# TODO:  
@dataclass 
class LocalPlan:
    path: list[tuple[float, float]] = field(default_factory=list)
    velocity: list[float] = field(default_factory=list)

    trajectory: Optional[TrajectoryTracker] = None

    
