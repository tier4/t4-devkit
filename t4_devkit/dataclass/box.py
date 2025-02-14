from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import numpy as np
from attrs import define, field
from attrs.converters import optional
from shapely.geometry import Polygon
from typing_extensions import Self

from t4_devkit.common.converter import to_quaternion

from .roi import Roi
from .trajectory import to_trajectories

if TYPE_CHECKING:
    from t4_devkit.dataclass import HomogeneousMatrix
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


__all__ = ["Box3D", "Box2D", "BoxType", "distance_box"]


def distance_box(box: BoxType, tf_matrix: HomogeneousMatrix) -> float | None:
    """Return a box distance from `base_link`.

    Args:
        box (BoxType): A box.
        tf_matrix (HomogeneousMatrix): Transformation matrix.

    Raises:
        TypeError: Expecting type of box is `Box2D` or `Box3D`.

    Returns:
        float | None: Return `None` if the type of box is `Box2D` and its `position` is `None`,
            otherwise returns distance from `base_link`.
    """
    if isinstance(box, Box2D) and box.position is None:
        return None

    if isinstance(box, Box2D):
        position = tf_matrix.transform(box.position)
    elif isinstance(box, Box3D):
        position, _ = tf_matrix.transform(box.position, box.rotation)
    else:
        raise TypeError(f"Unexpected box type: {type(box)}")

    return np.linalg.norm(position)


@define(eq=False)
class BaseBox:
    """Abstract base class for box objects."""

    unix_time: int
    frame_id: str
    semantic_label: SemanticLabel
    confidence: float = field(default=1.0, kw_only=True)
    uuid: str | None = field(default=None, kw_only=True)


# TODO: add intermediate class to represent the box state.
# >>> e.g.) box.as_state() -> BoxState


@define(eq=False)
class Box3D(BaseBox):
    """A class to represent 3D box.

    Attributes:
        unix_time (int): Unix timestamp.
        frame_id (str): Coordinates frame ID where the box is with respect to.
        semantic_label (SemanticLabel): `SemanticLabel` object.
        confidence (float, optional): Confidence score of the box.
        uuid (str | None, optional): Unique box identifier.
        position (TranslationType): Box center position (x, y, z).
        rotation (RotationType): Box rotation quaternion.
        shape (Shape): `Shape` object.
        velocity (VelocityType | None, optional): Box velocity (vx, vy, vz).
        num_points (int | None, optional): The number of points inside the box.
        future (list[Trajectory] | None, optional): Box trajectory in the future of each mode.

    Examples:
        >>> # without future
        >>> box3d = Box3D(
        ...     unix_time=100,
        ...     frame_id="base_link",
        ...     semantic_label=SemanticLabel("car"),
        ...     position=(1.0, 1.0, 1.0),
        ...     rotation=Quaternion([0.0, 0.0, 0.0, 1.0]),
        ...     shape=Shape(shape_type=ShapeType.BOUNDING_BOX, size=(1.0, 1.0, 1.0)),
        ...     velocity=(1.0, 1.0, 1.0),
        ...     confidence=1.0,
        ...     uuid="car3d_0",
        ... )
        >>> # with future
        >>> box3d = box3d.with_future(
        ...     waypoints=[[[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]],
        ...     confidences=[1.0],
        ... )
    """

    position: TranslationType = field(converter=np.array)
    rotation: RotationType = field(converter=to_quaternion)
    shape: Shape
    velocity: VelocityType | None = field(default=None, converter=optional(np.array))
    num_points: int | None = field(default=None)

    # additional attributes: set by `with_**`
    future: list[Trajectory] | None = field(default=None)

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
        """Return the box size in the order of (width, length, height).

        Returns:
            (width, length, height) values.
        """
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

    def translate(self, x: TranslationType) -> None:
        """Apply a translation.

        Args:
            x (TranslationType): 3D translation vector in the order of (x, y, z).
        """
        self.position += x

        if self.future is not None:
            self.future = [t.translate(x) for t in self.future]

    def rotate(self, q: RotationType) -> None:
        """Apply a rotation.

        Args:
            q (RotationType): Rotation quaternion.
        """
        self.position = np.dot(q.rotation_matrix, self.position)
        self.rotation = q * self.rotation

        if self.velocity is not None:
            self.velocity = np.dot(q.rotation_matrix, self.velocity)

        if self.future is not None:
            self.future = [t.rotate(q) for t in self.future]

    def corners(self, box_scale: float = 1.0) -> NDArrayF64:
        """Return the bounding box corners.

        Args:
            box_scale (float, optional): Multiply size by this factor to scale the box.

        Returns:
            First four corners are the ones facing forward. The last four are the ones facing backwards,
                in the shape of (8, 3).
        """
        width, length, height = self.size * box_scale

        # 3D box corners (Convention: x points forward, y to the left, z up.)
        x_corners = 0.5 * length * np.array([1, 1, 1, 1, -1, -1, -1, -1])
        y_corners = 0.5 * width * np.array([1, -1, -1, 1, 1, -1, -1, 1])
        z_corners = 0.5 * height * np.array([1, 1, -1, -1, 1, 1, -1, -1])
        corners = np.vstack((x_corners, y_corners, z_corners))  # (3, 8)

        # Rotate and translate
        return np.dot(self.rotation.rotation_matrix, corners).T + self.position


@define(eq=False)
class Box2D(BaseBox):
    """A class to represent 2D box.

    Attributes:
        unix_time (int): Unix timestamp.
        frame_id (str): Coordinates frame ID where the box is with respect to.
        semantic_label (SemanticLabel): `SemanticLabel` object.
        confidence (float, optional): Confidence score of the box.
        uuid (str | None, optional): Unique box identifier.
        roi (Roi | None, optional): `Roi` object.
        position (TranslationType | None, optional): 3D position (x, y, z).

    Examples:
        >>> # without 3D position
        >>> box2d = Box2D(
        ...     unix_time=100,
        ...     frame_id="camera",
        ...     semantic_label=SemanticLabel("car"),
        ...     roi=(100, 100, 50, 50),
        ...     confidence=1.0,
        ...     uuid="car2d_0",
        ... )
        >>> # with 3D position
        >>> box2d = box2d.with_position(position=(1.0, 1.0, 1.0))
    """

    roi: Roi | None = field(default=None, converter=lambda x: None if x is None else Roi(x))

    # additional attributes: set by `with_**`
    position: TranslationType | None = field(default=None)

    def with_position(self, position: TranslationType) -> Self:
        """Return a self instance setting `position` attribute.

        Args:
            position (TranslationType): 3D position.

        Returns:
            Self instance after setting `position`.
        """
        self.position = np.asarray(position)
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
    def offset(self) -> tuple[int, int] | None:
        return None if self.roi is None else self.roi.offset

    @property
    def size(self) -> tuple[int, int] | None:
        return None if self.roi is None else self.roi.size

    @property
    def width(self) -> int | None:
        return None if self.roi is None else self.roi.width

    @property
    def height(self) -> int | None:
        return None if self.roi is None else self.roi.height

    @property
    def center(self) -> tuple[int, int] | None:
        return None if self.roi is None else self.roi.center

    @property
    def area(self) -> int | None:
        return None if self.roi is None else self.roi.area


# type aliases
BoxType = TypeVar("BoxType", bound=BaseBox)
