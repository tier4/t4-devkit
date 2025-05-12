from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

import numpy as np

from t4_devkit.dataclass import Box3D, HomogeneousMatrix, ShapeType

from .utility import compute_area_intersection, compute_volume_intersection

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxLike
    from t4_devkit.typing import Vector3Like

__all__ = [
    "MatchingScorerLike",
    "CenterDistance",
    "PlaneDistance",
    "Iou2D",
    "Iou3D",
    "HeadingYaw",
]


# ===== Base Class for Matching Scorer =====


class MatchingScorerImpl(ABC):
    """Abstract base class of the function of matching scorer."""

    def __call__(
        self,
        box1: BoxLike,
        box2: BoxLike,
        ego2map: HomogeneousMatrix | None = None,
    ) -> float:
        self._validate(box1, box2)
        return self._calculate_score(box1, box2, ego2map)

    def _validate(self, box1: BoxLike, box2: BoxLike) -> None:
        """Validate the input two boxes.

        Args:
            box1 (BoxLike): A box.
            box2 (BoxLike): A box.

        Raises:
            TypeError: Expecting two boxes have the same type.
        """
        if not isinstance(box1, type(box2)):
            raise TypeError(
                f"Both boxes must be the same type, but got {type(box1)} and {type(box2)}."
            )

    def is_better_than(self, score: float, threshold: float) -> bool:
        """Check if the matching score of the input boxes satisfies the threshold.

        Args:
            score (float): Matching score.
            threshold (float): Threshold value of the matching score.

        Returns:
            Returns `True` the calculated matching score is better than the threshold.
        """
        return score <= threshold if self.is_smaller_score_better() else threshold <= score

    @classmethod
    @abstractmethod
    def is_smaller_score_better(cls) -> bool:
        """Indicate whether the smaller matching score is better.

        Returns:
            Returns `True` if the smaller score is better.
        """
        pass

    @abstractmethod
    def _calculate_score(
        self,
        box1: BoxLike,
        box2: BoxLike,
        ego2map: HomogeneousMatrix | None = None,
    ) -> float:
        """Calculate the matching score of the input two boxes.

        Args:
            box1 (BoxLike): A box.
            box2 (BoxLike): A box.
            ego2map (HomogeneousMatrix | None, optional): Transformation matrix from map to ego frame.

        Returns:
            Calculated matching score.
        """
        pass


MatchingScorerLike = TypeVar("MatchingScorer", bound=MatchingScorerImpl)

# ===== Specific Matching Scorers =====


class CenterDistance(MatchingScorerImpl):
    @classmethod
    def is_smaller_score_better(cls) -> bool:
        return True

    def _calculate_score(
        self,
        box1: BoxLike,
        box2: BoxLike,
        _ego2map: HomogeneousMatrix | None = None,
    ) -> float:
        return (
            np.linalg.norm(box1.position - box2.position)
            if isinstance(box1, Box3D)
            else np.linalg.norm(box1.center - box2.center)
        )


class PlaneDistance(MatchingScorerImpl):
    def _validate(self, box1, box2):
        super()._validate(box1, box2)

        if not isinstance(box1, Box3D):
            raise TypeError("For PlaneDistance, input boxes must be 3D.")

    @classmethod
    def is_smaller_score_better(cls) -> bool:
        return True

    def _calculate_score(
        self,
        box1: Box3D,
        box2: Box3D,
        ego2map: HomogeneousMatrix | None = None,
    ) -> float:
        box1 = self._transform2ego(box1, ego2map)
        box2 = self._transform2ego(box2, ego2map)

        if (
            box1.shape.shape_type == ShapeType.BOUNDING_BOX
            and box2.shape.shape_type == ShapeType.BOUNDING_BOX
        ):
            footprint1 = np.array(box1.footprint.exterior.coords)[:-1]
            footprint2 = np.array(box2.footprint.exterior.coords)[:-1]

            if box1.diff_yaw(box2) > 0.5 * np.pi:
                footprint1 = footprint1[[1, 0, 3, 2, 1]]

            sort_idx = np.argsort(np.linalg.norm(footprint2[:, :2], axis=1))

            sorted_footprint1 = footprint1[sort_idx]
            sorted_footprint2 = footprint2[sort_idx]

            left1, right1 = self._point_left_and_right(sorted_footprint1[0], sorted_footprint1[1])
            left2, right2 = self._point_left_and_right(sorted_footprint2[0], sorted_footprint2[1])

            distance_left = np.linalg.norm(left1[:2] - left2[:2])
            distance_right = np.linalg.norm(right1[:2] - right2[:2])

            distance = round(np.sqrt(0.5 * (distance_left**2 + distance_right**2)), 10)
        else:
            distance = np.linalg.norm(box1.position[:2] - box2.position[:2])

        return distance

    def _transform2ego(self, box: Box3D, ego2map: HomogeneousMatrix | None = None) -> Box3D:
        """Transform the box to base link frame if it is not.

        Todo:
            This method should be function.
        """
        if box.frame_id == "base_link":
            return box

        if ego2map is None:
            raise ValueError(f"For {box.frame_id}, `ego2map` must be specified.")

        matrix = HomogeneousMatrix(
            position=box.position,
            rotation=box.rotation,
            src=box.frame_id,
            dst="base_link",
        )

        tf = ego2map.inv().transform(matrix=matrix)

        return Box3D(
            unix_time=box.unix_time,
            frame_id="base_link",
            semantic_label=box.semantic_label,
            position=tf.position,
            rotation=tf.rotation,
            shape=box.shape,
            velocity=box.velocity,
            num_points=box.num_points,
            future=box.future,
            confidence=box.confidence,
            uuid=box.uuid,
        )

    def _point_left_and_right(
        self,
        point1: Vector3Like,
        point2: Vector3Like,
    ) -> tuple[Vector3Like, Vector3Like]:
        """Determine the input point is left or right."""
        cross_product = np.round(np.cross(point1[:2], point2[:2]), 10)
        return (point1, point2) if cross_product < 0 else (point2, point1)


class Iou2D(MatchingScorerImpl):
    @classmethod
    def is_smaller_score_better(cls) -> bool:
        return False

    def _calculate_score(
        self,
        box1: BoxLike,
        box2: BoxLike,
        _ego2map: HomogeneousMatrix | None = None,
    ) -> float:
        intersection = compute_area_intersection(box1, box2)
        union = box1.area + box2.area - intersection
        return intersection / union


class Iou3D(MatchingScorerImpl):
    def _validate(self, box1, box2):
        super()._validate(box1, box2)

        if not isinstance(box1, Box3D):
            raise TypeError("For Iou3D, input boxes must be 3D.")

    @classmethod
    def is_smaller_score_better(cls) -> bool:
        return False

    def _calculate_score(
        self,
        box1: Box3D,
        box2: Box3D,
        _ego2map: HomogeneousMatrix | None = None,
    ) -> float:
        intersection = compute_volume_intersection(box1, box2)
        union = box1.volume + box2.volume - intersection
        return intersection / union


class HeadingYaw(MatchingScorerImpl):
    def _validate(self, box1, box2):
        super()._validate(box1, box2)

        if not isinstance(box1, Box3D):
            raise TypeError("For Iou3D, input boxes must be 3D.")

    @classmethod
    def is_smaller_score_better(cls) -> bool:
        return True

    def _calculate_score(
        self,
        box1: Box3D,
        box2: Box3D,
        ego2map: HomogeneousMatrix | None = None,
    ) -> float:
        box1 = self._transform2ego(box1, ego2map)
        box2 = self._transform2ego(box2, ego2map)

        return abs(box2.diff_yaw(box1))

    def _transform2ego(self, box: Box3D, ego2map: HomogeneousMatrix | None = None) -> Box3D:
        """Transform the box to base link frame if it is not.

        Todo:
            This method should be function.
        """
        if box.frame_id == "base_link":
            return box

        if ego2map is None:
            raise ValueError(f"For {box.frame_id}, `ego2map` must be specified.")

        matrix = HomogeneousMatrix(
            position=box.position,
            rotation=box.rotation,
            src=box.frame_id,
            dst="base_link",
        )

        tf = ego2map.inv().transform(matrix=matrix)

        return Box3D(
            unix_time=box.unix_time,
            frame_id="base_link",
            semantic_label=box.semantic_label,
            position=tf.position,
            rotation=tf.rotation,
            shape=box.shape,
            velocity=box.velocity,
            num_points=box.num_points,
            future=box.future,
            confidence=box.confidence,
            uuid=box.uuid,
        )
