from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

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
    """Abstract base class of the matching policy functions."""

    @abstractmethod
    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        """Check if the input boxes satisfy the policy requirements.

        Args:
            box1 (BoxType): A box.
            box2 (BoxType): A box.

        Returns:
            bool: Return `True` if the input boxes satisfied the policy requirements.
        """
        pass


class StrictPolicy(MatchingPolicyImpl):
    """This policy allows the case only if the two boxes have the same label."""

    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        return box1.semantic_label == box2.semantic_label


class AllowUnknownPolicy(MatchingPolicyImpl):
    """This policy allows the case if the two boxes have the same label
    or one of boxes have the `UNKNOWN`."""

    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        return (
            box1.semantic_label == box2.semantic_label
            or box1.semantic_label.name.upper() == "UNKNOWN"
            or box2.semantic_label.name.upper() == "UNKNOWN"
        )


class AllowAnyPolicy(MatchingPolicyImpl):
    """This policy allows any cases."""

    def is_matchable(self, box1: BoxType, box2: BoxType) -> bool:
        return True


MatchingPolicyLike = TypeVar("MatchingPolicyLike", bound=MatchingPolicyImpl)
