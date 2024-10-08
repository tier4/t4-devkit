from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

import numpy as np
from pyquaternion import Quaternion
from shapely.geometry import Polygon
from typing_extensions import Self

from .roi import Roi
from .trajectory import to_trajectories

if TYPE_CHECKING:
    from t4_devkit.typing import (
        NDArrayF64,
        RotationType,
        SizeType,
        TrajectoryType,
        TranslationType,
        VelocityType,
    )

    from .label import SemanticLabel
    from .shape import Shape
    from .trajectory import Trajectory


__all__ = ["Box3D", "Box2D", "BoxType"]


@dataclass(eq=False)
class BaseBox:
    """Abstract base class for box objects."""

    unix_time: int
    frame_id: str
    semantic_label: SemanticLabel
    confidence: float = field(default=1.0, kw_only=True)
    uuid: str | None = field(default=None, kw_only=True)


@dataclass(eq=False)
class Box3D(BaseBox):
    """A class to represent 3D box."""

    position: TranslationType
    rotation: RotationType
    shape: Shape
    velocity: VelocityType | None = field(default=None)

    # additional attributes: set by `with_**`
    future: list[Trajectory] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.position, np.ndarray):
            self.position = np.array(self.position)

        if not isinstance(self.rotation, Quaternion):
            self.rotation = Quaternion(self.rotation)

        if self.velocity is not None and not isinstance(self.velocity, np.ndarray):
            self.velocity = np.array(self.velocity)

    def with_future(
        self,
        waypoints: list[TrajectoryType],
        confidences: list[float],
    ) -> Self:
        """Return a self instance setting `future` attribute.

        Args:
            waypoints (list[TrajectoryType]): List of waypoints for each mode.
            confidences (list[float]): List of confidences for each mode.

        Returns:
            Self instance after setting `future`.
        """
        self.future = to_trajectories(waypoints, confidences)
        return self

    def __eq__(self, other: Box3D | None) -> bool:
        if other is None:
            return False
        else:
            # NOTE: This comparison might be not enough
            eq = True
            eq &= self.unix_time == other.unix_time
            eq &= self.semantic_label == other.semantic_label
            eq &= self.position == other.position
            eq &= self.rotation == other.rotation
            return eq

    @property
    def size(self) -> SizeType:
        return self.shape.size

    @property
    def footprint(self) -> Polygon:
        return self.shape.footprint

    @property
    def area(self) -> float:
        return self.shape.footprint.area

    @property
    def volume(self) -> float:
        return self.area * self.size[2]

    def corners(self, box_scale: float = 1.0) -> NDArrayF64:
        """Return the bounding box corners.

        Args:
            box_scale (float, optional): Multiply size by this factor to scale the box.

        Returns:
            First four corners are the ones facing forward. The last four are the ones facing backwards,
                in the shape of (8, 3).
        """
        length, width, height = self.size * box_scale

        # 3D box corners (Convention: x points forward, y to the left, z up.)
        x_corners = 0.5 * length * np.array([1, 1, 1, 1, -1, -1, -1, -1])
        y_corners = 0.5 * width * np.array([1, -1, -1, 1, 1, -1, -1, 1])
        z_corners = 0.5 * height * np.array([1, 1, -1, -1, 1, 1, -1, -1])
        corners = np.vstack((x_corners, y_corners, z_corners))  # (3, 8)

        # Rotate and translate
        return np.dot(self.rotation.rotation_matrix, corners).T + self.position


@dataclass(eq=False)
class Box2D(BaseBox):
    """A class to represent 2D box."""

    roi: Roi | None = field(default=None)

    # additional attributes: set by `with_**`
    position: TranslationType | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.roi is not None and not isinstance(self.roi, Roi):
            self.roi = Roi(self.roi)

    def with_position(self, position: TranslationType) -> Self:
        """Return a self instance setting `position` attribute.

        Args:
            position (TranslationType): 3D position.

        Returns:
            Self instance after setting `position`.
        """
        self.position = position
        return self

    def __eq__(self, other: Box2D | None) -> bool:
        if other is None:
            return False
        else:
            # NOTE: This comparison might be not enough
            eq = True
            eq &= self.unix_time == other.unix_time
            eq &= self.semantic_label == other.semantic_label
            return eq

    @property
    def area(self) -> int:
        return -1 if self.roi is None else self.roi.area


# type aliases
BoxType = TypeVar("BoxType", bound=BaseBox)
