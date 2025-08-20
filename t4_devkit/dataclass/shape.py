from __future__ import annotations

from enum import Enum, auto, unique
from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field
from shapely.geometry import Polygon
from typing_extensions import Self

from t4_devkit.typing import Vector3

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayF64


__all__ = ["ShapeType", "Shape"]


@unique
class ShapeType(Enum):
    BOUNDING_BOX = 0
    POLYGON = auto()

    @classmethod
    def from_name(cls, name: str) -> Self:
        """Return an enum object from the name of the member.

        Args:
            name (str): Name of enum member.

        Returns:
            Enum object.
        """
        name = name.upper()
        assert name in cls.__members__, f"Unexpected shape type: {name}."
        return cls.__members__[name]


@define
class Shape:
    """A dataclass to represent the 3D box shape.

    Attributes:
        shape_type (ShapeType): Box shape type.
        size (Vector3): Box size in the order of (width, length, height).
        footprint (Polygon): Polygon of footprint.

    Examples:
        >>> shape = Shape(
        ...     shape_type=ShapeType.BOUNDING_BOX,
        ...     size=[1.0, 1.0, 1.0]
        ... )
    """

    shape_type: ShapeType
    size: Vector3 = field(converter=Vector3)
    footprint: Polygon = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.shape_type == ShapeType.POLYGON and self.footprint is None:
            raise ValueError("`footprint` must be specified for `POLYGON`.")

        if self.footprint is None:
            self.footprint = _calculate_footprint(self.size)


def _calculate_footprint(size: Vector3) -> Polygon:
    """Return a footprint of box as `Polygon` object.

    Args:
        size (Vector3): Size of box ordering in (width, length, height).

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
