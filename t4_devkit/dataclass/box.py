from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import numpy as np
from attrs import converters, define, field, validators
from shapely.geometry import Polygon
from typing_extensions import Self

from t4_devkit.common.converter import to_quaternion
from t4_devkit.schema import VisibilityLevel
from t4_devkit.typing import Quaternion, Roi, Vector3

from .label import SemanticLabel
from .shape import Shape
from .trajectory import Future

if TYPE_CHECKING:
    from t4_devkit.dataclass import HomogeneousMatrix
    from t4_devkit.typing import ArrayLike, NDArrayF64, RotationLike, ScalarLike, Vector3Like


__all__ = ["Box3D", "Box2D", "BoxLike", "distance_box"]


def distance_box(box: BoxLike, tf_matrix: HomogeneousMatrix) -> float | None:
    """Return a box distance from `base_link`.

    Args:
        box (BoxLike): A box.
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

    return np.linalg.norm(position).item()


@define(eq=False)
class BaseBox:
    """Abstract base class for box objects."""

    unix_time: int = field(validator=validators.instance_of(int))
    frame_id: str = field(validator=validators.instance_of(str))
    semantic_label: SemanticLabel = field(validator=validators.instance_of(SemanticLabel))
    confidence: float = field(
        default=1.0,
        validator=[validators.ge(0.0), validators.le(1.0)],
        kw_only=True,
    )
    uuid: str | None = field(
        default=None,
        validator=validators.optional(validators.instance_of(str)),
        kw_only=True,
    )


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
        position (Vector3): Box center position (x, y, z).
        rotation (Quaternion): Box rotation quaternion.
        shape (Shape): `Shape` object.
        velocity (Vector3 | None, optional): Box velocity (vx, vy, vz).
        num_points (int | None, optional): The number of points inside the box.
        visibility (VisibilityLevel, optional): Box visibility.
        future (Future | None, optional): Box trajectory in the future of each mode.

    Examples:
        >>> # without future
        >>> box3d = Box3D(
        ...     unix_time=100,
        ...     frame_id="base_link",
        ...     semantic_label=SemanticLabel("car"),
        ...     position=(1.0, 1.0, 1.0),
        ...     rotation=(0.0, 0.0, 0.0, 1.0),
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

    position: Vector3 = field(converter=Vector3)
    rotation: Quaternion = field(converter=to_quaternion)
    shape: Shape = field(validator=validators.instance_of(Shape))
    velocity: Vector3 | None = field(default=None, converter=converters.optional(Vector3))
    num_points: int | None = field(
        default=None,
        validator=validators.optional((validators.instance_of(int), validators.ge(0))),
    )
    visibility: VisibilityLevel = field(
        default=VisibilityLevel.UNAVAILABLE,
        converter=VisibilityLevel,
        validator=validators.instance_of(VisibilityLevel),
    )

    # additional attributes: set by `with_**`
    future: Future | None = field(
        default=None,
        validator=validators.optional(validators.instance_of(Future)),
    )

    def with_future(
        self,
        timestamps: ArrayLike,
        confidences: ArrayLike,
        waypoints: ArrayLike,
    ) -> Self:
        """Return a self instance setting `future` attribute.

        Args:
            timestamps (ArrayLike): Array of future timestamps at each waypoint in the shape of (T).
            confidences (ArrayLike): Array of confidences for each mode in the shape of (M).
            waypoints (ArrayLike): Array of waypoints for each mode in the shape of (M, T, D).

        Returns:
            Self instance after setting `future`.
        """
        self.future = Future(timestamps=timestamps, confidences=confidences, waypoints=waypoints)
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
    def size(self) -> Vector3:
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

    def translate(self, x: Vector3Like) -> None:
        """Apply a translation.

        Args:
            x (Vector3Like): 3D translation vector in the order of (x, y, z).
        """
        self.position += Vector3(x)

        if self.future is not None:
            self.future.translate(x)

    def rotate(self, q: RotationLike) -> None:
        """Apply a rotation.

        Args:
            q (RotationLike): Rotation quaternion.
        """
        q = to_quaternion(q)
        self.position = np.dot(q.rotation_matrix, self.position)
        self.rotation = q * self.rotation

        if self.velocity is not None:
            self.velocity = np.dot(q.rotation_matrix, self.velocity)

        if self.future is not None:
            self.future.rotate(q)

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

    def diff_yaw(self, other: Box3D) -> float:
        """Return the yaw difference between the two boxes.

        Args:
            other (Box3D): Another box.

        Raises:
            ValueError: Both boxes must have the same `frame_id`.

        Returns:
            Yaw difference in the range of [-pi, pi].
        """
        if self.frame_id != other.frame_id:
            raise ValueError(f"Invalid frame comparison: {self.frame_id=} and {other.frame_id=}")

        yaw1, *_ = self.rotation.yaw_pitch_roll
        yaw2, *_ = other.rotation.yaw_pitch_roll

        def _clip(diff: float) -> float:
            if diff < -np.pi:
                diff += 2 * np.pi
            elif diff > np.pi:
                diff -= 2 * np.pi
            return diff

        return _clip(yaw2 - yaw1)


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
        position (Vector3 | None, optional): 3D position (x, y, z).

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

    roi: Roi | None = field(
        default=None,
        converter=lambda x: None if x is None else Roi(x),
    )

    # additional attributes: set by `with_**`
    position: Vector3 | None = field(
        default=None,
        converter=lambda x: None if x is None else Vector3(x),
    )

    def with_position(self, position: Vector3Like) -> Self:
        """Return a self instance setting `position` attribute.

        Args:
            position (Vector3Like): 3D position.

        Returns:
            Self instance after setting `position`.
        """
        self.position = Vector3(position)
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
    def offset(self) -> tuple[ScalarLike, ScalarLike] | None:
        return None if self.roi is None else self.roi.offset

    @property
    def size(self) -> tuple[ScalarLike, ScalarLike] | None:
        return None if self.roi is None else self.roi.size

    @property
    def width(self) -> ScalarLike | None:
        return None if self.roi is None else self.roi.width

    @property
    def height(self) -> ScalarLike | None:
        return None if self.roi is None else self.roi.height

    @property
    def center(self) -> tuple[ScalarLike, ScalarLike] | None:
        return None if self.roi is None else self.roi.center

    @property
    def area(self) -> ScalarLike | None:
        return None if self.roi is None else self.roi.area


# type aliases
BoxLike = TypeVar("BoxLike", bound=BaseBox)
