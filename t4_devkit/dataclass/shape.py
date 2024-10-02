from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto, unique
from typing import TYPE_CHECKING

import numpy as np
from shapely.geometry import Polygon
from typing_extensions import Self

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayF64, SizeType


__all__ = ["ShapeType", "Shape"]


@unique
class ShapeType(Enum):
    BOUNDING_BOX = auto()
    POLYGON = auto()

    @classmethod
    def from_name(cls, name: str) -> Self:
        name = name.upper()
        assert name in cls.__members__, f"Unexpected shape type: {name}."
        return cls.__members__[name]


@dataclass
class Shape:
    shape_type: ShapeType
    size: SizeType
    footprint: Polygon = field(default=None)

    def __post_init__(self) -> None:
        if not isinstance(self.size, np.ndarray):
            self.size = np.array(self.size)

        if self.shape_type == ShapeType.POLYGON and self.footprint is None:
            raise ValueError("`footprint` must be specified for `POLYGON`.")

        if self.footprint is None:
            self.footprint = _calculate_footprint(self.size)


def _calculate_footprint(size: SizeType) -> Polygon:
    """Return a footprint of box as `Polygon` object.

    Args:
        size (SizeType): Size of box ordering in (length, width, height).

    Returns:
        Footprint in a clockwise order started from the top-right corner.
    """

    corners: list[NDArrayF64] = [
        np.array([size[1], size[0], 0.0]) / 2.0,
        np.array([-size[1], size[0], 0.0]) / 2.0,
        np.array([-size[1], -size[0], 0.0]) / 2.0,
        np.array([size[1], -size[0], 0.0]) / 2.0,
    ]

    return Polygon(
        [
            corners[0],
            corners[1],
            corners[2],
            corners[3],
            corners[0],
        ]
    )
