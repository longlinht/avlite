"""Compatibility bridge types for pre-0.5 external plugins.

Execution itself uses the current c41/c42 implementation. This module only
maps the former mixed capability enum onto the split world/stack contracts.
"""

from abc import abstractmethod

from avlite.c40_execution.c41_world_bridge import WorldBridge as CurrentWorldBridge
from avlite.c40_execution.c42_execution_strategy import ExecutionStrategy as Executer
from avlite.c50_common.c51_capabilities import (
    StackCapability,
    WorldCapability as CurrentWorldCapability,
)


class WorldBridge(CurrentWorldBridge, abstract=True):
    @property
    @abstractmethod
    def capabilities(self):
        """Return capabilities in the legacy combined enum."""

    @property
    def world_capabilities(self) -> frozenset[CurrentWorldCapability]:
        sensor_names = {cap.name for cap in self.capabilities}
        return frozenset(
            cap for cap in CurrentWorldCapability if cap.name in sensor_names
        )

    @property
    def stack_capabilities(self) -> frozenset[StackCapability]:
        names = {cap.name for cap in self.capabilities}
        mapping = {
            "GT_DETECTION": StackCapability.DETECTION,
            "GT_TRACKING": StackCapability.TRACKING,
            "GT_LOCALIZATION": StackCapability.LOCALIZATION,
        }
        return frozenset(mapping[name] for name in mapping if name in names)


__all__ = ["Executer", "WorldBridge"]
