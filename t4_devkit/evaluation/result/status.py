from __future__ import annotations

from enum import Enum

__all__ = ["MatchingStatus"]


class MatchingStatus(str, Enum):
    TP = "TP"
    FP = "FP"
    FN = "FN"
    TN = "TN"

    def is_positive(self) -> bool:
        return self in ("TP", "FP")

    def is_negative(self) -> bool:
        return self in ("TN", "FN")

    def is_true(self) -> bool:
        return self in ("TP", "TN")

    def is_false(self) -> bool:
        return self in ("FP", "FN")
