from __future__ import annotations

from enum import Enum, unique
from typing import TYPE_CHECKING

import matplotlib
import numpy as np

if TYPE_CHECKING:
    from t4_devkit.dataclass import PointCloudLike
    from t4_devkit.typing import ArrayLike, NDArrayF64


__all__ = ["PointCloudColorMode", "pointcloud_color"]


@unique
class PointCloudColorMode(str, Enum):
    """Color mode of point cloud."""

    DISTANCE = "distance"
    INTENSITY = "intensity"
    SEGMENTATION = "segmentation"


def pointcloud_color(
    pointcloud: PointCloudLike,
    color_mode: PointCloudColorMode = PointCloudColorMode.DISTANCE,
) -> NDArrayF64:
    """Return color map depending on the specified color mode.

    Args:
        pointcloud (PointCloudLike): Any inheritance of `PointCloud` class.
        color_mode (PointCloudColorMode, optional): Color mode for pointcloud.

    Returns:
        NDArrayF64: RGB color array in the shape of (N, 3).
    """
    match color_mode:
        case PointCloudColorMode.DISTANCE:
            values = np.linalg.norm(pointcloud.points[:3].T, axis=1)
        case PointCloudColorMode.INTENSITY:
            values = pointcloud.points[3]
        case _:
            raise ValueError(f"Unsupported color mode: {color_mode}")

    return _normalize_color(values)


def _normalize_color(values: ArrayLike, cmap: str | None = None, alpha: float = 1.0) -> NDArrayF64:
    """Return color map normalizing values.

    Args:
        values (ArrayLike): Array of values in the shape of (N,).
        cmap (str | None, optional): Color map name in matplotlib. If None, `turbo_r` will be used.
        alpha (float, optional): Alpha value of color map.

    Returns:
        Color map in the shape of (N,).
    """
    color_map = matplotlib.colormaps["turbo_r"] if cmap is None else matplotlib.colormaps[cmap]
    v_min = np.min(values)
    v_max = np.max(values)
    norm = matplotlib.colors.Normalize(v_min, v_max)
    return color_map(norm(values), alpha=alpha)
