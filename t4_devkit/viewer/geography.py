from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from t4_devkit.typing import Vector2, Vector3

if TYPE_CHECKING:
    from t4_devkit.typing import Vector2Like, Vector3Like

__all__ = ["calculate_geodetic_point"]

EARTH_RADIUS_METERS = 6.378137e6
FLATTENING = 1 / 298.257223563


def calculate_geodetic_point(position: Vector3Like, origin: Vector2Like) -> Vector2:
    """Transform a position in a map coordinate system to a position in a geodetic coordinate system.

    Args:
        position (Vector3Like): 3D position in a map coordinate system.
        origin (Vector2Like): Map origin position in a geodetic coordinate system,
            which is (latitude, longitude).

    Returns:
        Transformed position in a geodetic coordinate system, which is (latitude, longitude).
    """
    x, y, _ = Vector3(position)
    bearing = math.atan2(x, y)
    distance = math.hypot(x, y)

    latitude, longitude = np.radians(Vector2(origin))
    angular_distance = distance / EARTH_RADIUS_METERS

    target_latitude = math.asin(
        math.sin(latitude) * math.cos(angular_distance)
        + math.cos(latitude) * math.sin(angular_distance) * math.cos(bearing)
    )
    target_longitude = longitude + math.atan2(
        math.sin(bearing) * math.sin(angular_distance) * math.cos(latitude),
        math.cos(angular_distance) - math.sin(latitude) * math.sin(target_latitude),
    )

    return Vector2(math.degrees(target_latitude), math.degrees(target_longitude))
