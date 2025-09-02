from __future__ import annotations

from enum import Enum, unique
from typing import TYPE_CHECKING

import matplotlib
import numpy as np

if TYPE_CHECKING:
    from t4_devkit.dataclass import PointCloudLike
    from t4_devkit.typing import ArrayLike, NDArrayF64


@unique
class PointCloudColorMode(str, Enum):
    """Color mode of point cloud."""

    DISTANCE = "distance"
    INTENSITY = "intensity"


def pointcloud_color(
    pointcloud: PointCloudLike,
    color_mode: PointCloudColorMode = PointCloudColorMode.INTENSITY,
) -> NDArrayF64:
    """Return color map depending on the specified color mode.

    Args:
        pointcloud (PointCloudLike): Any inheritance of `PointCloud` class.
        color_mode (PointCloudColorMode): Color mode of point cloud.
    """
    match color_mode:
        case PointCloudColorMode.DISTANCE:
            values = np.linalg.norm(pointcloud.points[:3].T, axis=1)
        case _:
            values = pointcloud.points[3]

    return distance_color(values)


def distance_color(
    distances: ArrayLike,
    cmap: str | None = None,
) -> tuple[float, float, float] | NDArrayF64:
    """Return color map depending on distance values.

    Args:
        distances (ArrayLike): Array of distances in the shape of (N,).
        cmap (str | None, optional): Color map name in matplotlib. If None, `turbo_r` will be used.

    Returns:
        Color map in the shape of (N,). If input type is any number, returns a color as
            `tuple[float, float, float]`. Otherwise, returns colors as `NDArrayF64`.
    """
    color_map = matplotlib.colormaps["turbo_r"] if cmap is None else matplotlib.colormaps[cmap]
    v_min = np.min(distances)
    v_max = np.max(distances)
    norm = matplotlib.colors.Normalize(v_min, v_max)
    return color_map(norm(distances))
