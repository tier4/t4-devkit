from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from t4_devkit.dataclass import Box3D

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType

__all__ = [
    "MatchingScorerLike",
    "MatchingScorerImpl",
    "CenterDistance",
    "PlaneDistance",
    "Iou2D",
    "Iou3D",
]


class MatchingScorerImpl(ABC):
    def __call__(self, box1: BoxType, box2: BoxType) -> float:
        self._validate(box1, box2)
        return self._calculate_score(box1, box2)

    def _validate(self, box1: BoxType, box2: BoxType) -> None:
        if not isinstance(box1, type(box2)):
            raise TypeError(
                f"Both boxes must be the same type, but got {type(box1)} and {type(box2)}."
            )

    @abstractmethod
    @classmethod
    def smaller_is_better(cls) -> bool:
        pass

    @abstractmethod
    def _calculate_score(self, box1: BoxType, box2: BoxType) -> float:
        pass

    def is_better_than(self, score: float, threshold: float) -> bool:
        return score <= threshold if self.smaller_is_better() else threshold <= score


class CenterDistance(MatchingScorerImpl):
    @classmethod
    def smaller_is_better(cls) -> bool:
        return True

    def _calculate_score(self, box1: BoxType, Box2: BoxType) -> float:
        pass


class PlaneDistance(MatchingScorerImpl):
    def _validate(self, box1: BoxType, box2: BoxType) -> None:
        super()._validate(box1, box2)

        if not isinstance(box1, Box3D):
            raise TypeError(f"Both boxes must be Box3D, but got {type(box1)} and {type(box2)}.")

    @classmethod
    def smaller_is_better(cls) -> bool:
        return True

    def _calculate_score(self, box1: BoxType, Box2: BoxType) -> float:
        pass


class Iou2D(MatchingScorerImpl):
    @classmethod
    def smaller_is_better(cls) -> bool:
        return False

    def _calculate_score(self, box1: BoxType, box2: BoxType) -> float:
        pass


class Iou3D(MatchingScorerImpl):
    def _validate(self, box1: BoxType, box2: BoxType) -> None:
        super()._validate(box1, box2)

        if not isinstance(box1, Box3D):
            raise TypeError(f"Both boxes must be Box3D, but got {type(box1)} and {type(box2)}.")

    @classmethod
    def smaller_is_better(cls) -> bool:
        return False

    def _calculate_score(self, box1: BoxType, box2: BoxType) -> float:
        pass


MatchingScorerLike = TypeVar("MatchingScorer", bound=MatchingScorerImpl)
