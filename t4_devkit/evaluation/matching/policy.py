from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxLike


__all__ = [
    "MatchingPolicyLike",
    "StrictPolicy",
    "AllowUnknownPolicy",
    "AllowAnyPolicy",
]

# ===== Base Class for Matching Policy =====


class MatchingPolicyImpl(ABC):
    """Abstract base class of the matching policy functions."""

    @abstractmethod
    def is_matchable(self, box1: BoxLike, box2: BoxLike) -> bool:
        """Check if the input boxes satisfy the policy requirements.

        Args:
            box1 (BoxLike): A box.
            box2 (BoxLike): A box.

        Returns:
            bool: Return `True` if the input boxes satisfied the policy requirements.
        """
        pass


MatchingPolicyLike = TypeVar("MatchingPolicyLike", bound=MatchingPolicyImpl)


# ===== Specific Matching Policies =====


class StrictPolicy(MatchingPolicyImpl):
    """This policy allows the case only if the two boxes have the same label."""

    def is_matchable(self, box1: BoxLike, box2: BoxLike) -> bool:
        return box1.semantic_label == box2.semantic_label


class AllowUnknownPolicy(MatchingPolicyImpl):
    """This policy allows the case if the two boxes have the same label
    or one of boxes have the `UNKNOWN`."""

    def is_matchable(self, box1: BoxLike, box2: BoxLike) -> bool:
        return (
            box1.semantic_label == box2.semantic_label
            or box1.semantic_label.name.upper() == "UNKNOWN"
            or box2.semantic_label.name.upper() == "UNKNOWN"
        )


class AllowAnyPolicy(MatchingPolicyImpl):
    """This policy allows any cases."""

    def is_matchable(self, box1: BoxLike, box2: BoxLike) -> bool:
        return True
