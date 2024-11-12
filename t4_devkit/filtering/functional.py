from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence, TypeVar

import numpy as np
from typing_extensions import Self

from t4_devkit.dataclass import Box2D, Box3D, HomogeneousMatrix, distance_box
from t4_devkit.filtering.parameter import FilterParams

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType, SemanticLabel


__all__ = [
    "BaseBoxFilter",
    "FilterByLabel",
    "FilterByUUID",
    "FilterByDistance",
    "FilterByPosition",
    "BoxFilterFunction",
]


class BaseBoxFilter(ABC):
    """Abstract base class of box filter functions."""

    @classmethod
    @abstractmethod
    def from_params(cls, params: FilterParams) -> Self:
        """Construct a new object from `FilterParams`.

        Args:
            params (FilterParams): Filtering parameters.

        Returns:
            A new self object.
        """
        pass

    @abstractmethod
    def __call__(self, box: BoxType, tf_matrix: HomogeneousMatrix | None = None) -> bool:
        """Check whether the input box satisfies requirements.

        Args:
            box (BoxType): Box.
            tf_matrix (HomogeneousMatrix): Transformation matrix.

        Returns:
            Return `True` if the box satisfies requirements.
        """
        pass


class FilterByLabel(BaseBoxFilter):
    """Filter a box by checking if the label of the box is included in specified labels.

    Note that, if `labels` is None all boxes pass through this filter.
    """

    def __init__(self, labels: Sequence[str | SemanticLabel] | None = None) -> None:
        """Construct a new object.

        Args:
            labels (Sequence[str | SemanticLabel] | None, optional): Sequence of target labels.
                If `None`, this filter always returns `True`.
        """
        super().__init__()
        self.labels = labels

    @classmethod
    def from_params(cls, params: FilterParams) -> Self:
        return cls(params.labels)

    def __call__(self, box: BoxType, _tf_matrix: HomogeneousMatrix | None = None) -> bool:
        if self.labels is None:
            return True

        return box.semantic_label in self.labels


class FilterByUUID(BaseBoxFilter):
    """Filter a box by checking if the uuid of the box is included in specified uuids.

    Note that, if `uuids` is None all boxes pass through this filter.
    """

    def __init__(self, uuids: Sequence[str] | None = None) -> None:
        """Construct a new object.

        Args:
            uuids (Sequence[str] | None, optional): Sequence of target uuids.
                If `None`, this filter always returns `True`.
        """
        super().__init__()
        self.uuids = uuids

    @classmethod
    def from_params(cls, params: FilterParams) -> Self:
        return cls(params.uuids)

    def __call__(self, box: BoxType, _tf_matrix: HomogeneousMatrix | None = None) -> bool:
        if self.uuids is None:
            return True

        return box.uuid in self.uuids


class FilterByDistance(BaseBoxFilter):
    """Filter a box by checking if the box is within the specified distance.

    Note that, the type box is `Box2D` and its `position` is None,
    these boxes pass through this filter.
    """

    def __init__(self, min_distance: float, max_distance: float) -> None:
        """Construct a new object.

        Args:
            min_distance (float): Minimum distance from the ego [m].
            max_distance (float): Maximum distance from the ego [m].
        """
        super().__init__()
        self.min_distance = min_distance
        self.max_distance = max_distance

    @classmethod
    def from_params(cls, params: FilterParams) -> Self:
        return cls(params.min_distance, params.max_distance)

    def __call__(self, box: BoxType, tf_matrix: HomogeneousMatrix) -> bool:
        box_distance = distance_box(box, tf_matrix)

        # box_distance is None, only if the box is 2D and its position is None.
        if box_distance is None:
            return True
        else:
            return self.min_distance < box_distance and box_distance < self.max_distance


class FilterByPosition(BaseBoxFilter):
    """Filter a box by checking if the box xy position is within the specified xy position.

    Note that, the type box is `Box2D` and its `position` is None,
    these boxes pass through this filter.
    """

    def __init__(self, min_xy: tuple[float, float], max_xy: tuple[float, float]) -> None:
        """Construct a new object.

        Args:
            min_xy (tuple[float, float]): Minimum xy position [m].
            max_xy (tuple[float, float]): Maximum xy position [m].
        """
        super().__init__()
        self.min_xy = min_xy
        self.max_xy = max_xy

    @classmethod
    def from_params(cls, params: FilterParams) -> Self:
        return cls(params.min_xy, params.max_xy)

    def __call__(self, box: BoxType, tf_matrix: HomogeneousMatrix) -> bool:
        if isinstance(box, Box2D) and box.position is None:
            return True

        if isinstance(box, Box2D):
            position = tf_matrix.transform(box.position)
        elif isinstance(box, Box3D):
            position, _ = tf_matrix.transform(box.position, box.rotation)
        else:
            raise TypeError(f"Unexpected box type: {type(box)}")

        return np.all((self.min_xy < position[:2]) & (position[:2] < self.max_xy))


class FilterBySpeed(BaseBoxFilter):
    """Filter a 3D box by checking if the box speed is within the specified one.

    Note that, the type box is `Box2D`, or `Box3D` and its `velocity` is None,
    these boxes pass through this filter.
    """

    def __init__(self, min_speed: float, max_speed: float) -> None:
        """Construct a new object.

        Args:
            min_speed (float): Minimum speed [m/s].
            max_speed (float): Maximum speed [m/s].
        """
        super().__init__()
        self.min_speed = min_speed
        self.max_speed = max_speed

    @classmethod
    def from_params(cls, params: FilterParams) -> Self:
        return cls(params.min_speed, params.max_speed)

    def __call__(self, box: BoxType, _tf_matrix: HomogeneousMatrix | None = None) -> bool:
        if isinstance(box, Box2D):
            return True
        elif isinstance(box, Box3D) and box.velocity is None:
            return True
        else:
            speed = np.linalg.norm(box.velocity)
            return self.min_speed < speed and speed < self.max_speed


class FilterByNumPoints(BaseBoxFilter):
    """Filter a 3D box by checking if the box includes points greater than the specified one.

    Note that, the type box is `Box2D`, or `Box3D` and its `num_points` is None,
    these boxes pass through this filter.
    """

    def __init__(self, min_num_points: int = 0) -> None:
        """Construct a new object.

        Args:
            min_num_points (int, optional): The minimum number of points that a box should include.
        """
        super().__init__()
        self.min_num_points = min_num_points

    @classmethod
    def from_params(cls, params: FilterParams) -> Self:
        return cls(params.min_num_points)

    def __call__(self, box: BoxType, _tf_matrix: HomogeneousMatrix | None = None) -> bool:
        if isinstance(box, Box2D):
            return True
        elif isinstance(box, Box3D) and box.num_points is None:
            return True
        else:
            return self.min_num_points <= box.num_points


BoxFilterFunction = TypeVar("BoxFilterFunction", bound=BaseBoxFilter)
