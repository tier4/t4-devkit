from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from t4_devkit.typing import Vector3Like


__all__ = ["calculate_geodetic_point"]

EARTH_RADIUS_METERS = 6.378137e6
FLATTENING = 1 / 298.257223563


def calculate_geodetic_point(
    position: Vector3Like,
    origin: tuple[float, float],
) -> tuple[float, float]:
    """Transform a position in a map coordinate system to a position in a geodetic coordinate system.

    Args:
        position (Vector3Like): 3D position in a map coordinate system.
        origin (tuple[float, float]): Map origin position in a geodetic coordinate system,
            which is (latitude, longitude).

    Returns:
        tuple[float, float]: Transformed position in a geodetic coordinate system,
            which is (latitude, longitude).
    """
    x, y, _ = position
    bearing = math.atan2(x, y)
    distance = math.hypot(x, y)

    latitude, longitude = np.radians(origin)
    angular_distance = distance / EARTH_RADIUS_METERS

    target_latitude = math.asin(
        math.sin(latitude) * math.cos(angular_distance)
        + math.cos(latitude) * math.sin(angular_distance) * math.cos(bearing)
    )
    target_longitude = longitude + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(latitude),
        math.cos(angular_distance) - math.sin(latitude) * math.sin(target_latitude),
    )

    return math.degrees(target_latitude), math.degrees(target_longitude)
