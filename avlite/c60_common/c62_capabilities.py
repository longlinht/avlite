"""Legacy capability enums retained for pre-0.5 external plugins."""

from enum import Enum, auto


class WorldCapability(Enum):
    GT_DETECTION = auto()
    GT_TRACKING = auto()
    GT_LOCALIZATION = auto()
    CAMERA_RGB = auto()
    CAMERA_DEPTH = auto()
    LIDAR_3D = auto()
    LIDAR_2D = auto()
    RADAR = auto()
    WHEEL_ENCODER = auto()
    IMU = auto()
    GNSS = auto()


class PerceptionCapability(Enum):
    DETECTION = auto()
    TRACKING = auto()
    PREDICTION = auto()


class LocalizationCapability(Enum):
    LOCALIZATION_2D = auto()
    LOCALIZATION_3D = auto()
    LOCALIZATION_HEADING = auto()
    LOCALIZATION_HEADING_3D = auto()
    VELOCITY = auto()
    GNSS = auto()


class MappingCapability(Enum):
    OCCUPANCY_GRID = auto()
    PATH_BOUNDARY = auto()
    OPENDRIVE_HDMAP = auto()
