from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from t4_devkit.dataclass import LabelID

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType


__all__ = [
    "MatchingPolicyImpl",
    "MatchingPolicyLike",
    "StrictPolicy",
    "AllowUnknownPolicy",
    "AllowAnyPolicy",
]


class MatchingPolicyImpl(ABC):
    @abstractmethod
    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        pass


class StrictPolicy(MatchingPolicyImpl):
    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        return box1.semantic_label == box2.semantic_label


class AllowUnknownPolicy(MatchingPolicyImpl):
    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        return (
            box1.semantic_label == box2.semantic_label
            or box1.semantic_label.label == LabelID.UNKNOWN
            or box2.semantic_label.label == LabelID.UNKNOWN
        )


class AllowAnyPolicy(MatchingPolicyImpl):
    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        return True


MatchingPolicyLike = TypeVar("MatchingPolicyLike", bound=MatchingPolicyImpl)
