"""Compatibility imports for the trajectory tracker moved in AVLite 0.5."""

from avlite.c50_common.c54_trajectory_tracker import *  # noqa: F401,F403
from avlite.c50_common.c54_trajectory_tracker import TrajectoryTracker as _TrajectoryTracker


class TrajectoryTracker(_TrajectoryTracker):
    """Retain the legacy cyclic waypoint update contract for old plugins."""

    def update_waypoint_by_wp(self, current_wp: int) -> None:
        n = len(self.path)
        if n == 0:
            self.current_wp = 0
            self.next_wp = 0
            return
        self.current_wp = current_wp % n
        self.next_wp = (self.current_wp + 1) % n

    def update_to_next_waypoint(self) -> None:
        if self.path:
            self.update_waypoint_by_wp(self.current_wp + 1)
