from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box3D

__all__ = ["compute_area_intersection", "compute_volume_intersection"]


def compute_area_intersection(box1: Box3D, box2: Box3D) -> float:
    """Return the area intersection between two boxes.

    Args:
        box1 (Box3D): A box.
        box2 (Box3D): A box.

    Returns:
        float: Intersection of area.

    """
    # TODO(ktro2828): add support of 2D boxes
    return box1.footprint.intersection(box2.footprint).area


def compute_volume_intersection(box1: Box3D, box2: Box3D) -> float:
    """Return the volume intersection between two 3D boxes.

    Args:
        box1 (Box3D): A box.
        box2 (Box3D): A box.

    Returns:
        float: Intersection of volume.
    """
    area = compute_area_intersection(box1, box2)

    min_z = max(box1.position[2] - 0.5 * box1.size[2], box2.position[2] - 0.5 * box2.size[2])
    max_z = min(box1.position[2] + 0.5 * box1.size[2], box2.position[2] + 0.5 * box2.size[2])
    height = max(0, max_z - min_z)

    return area * height
