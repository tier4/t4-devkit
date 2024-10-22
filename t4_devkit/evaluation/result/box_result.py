from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field

from .status import MatchingStatus

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType
    from t4_devkit.evaluation import MatchingScorerLike

__all__ = ["PerceptionBoxResult"]


@define
class PerceptionBoxResult:
    estimation: BoxType | None = field(default=None)
    ground_truth: BoxType | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.estimation is None and self.ground_truth is None:
            raise ValueError("At least one of `estimation` or `ground_truth` must be set.")

    def is_label_ok(self) -> bool:
        return (
            False
            if self.estimation is None or self.ground_truth is None
            else self.estimation.semantic_label == self.ground_truth.semantic_label
        )

    def is_tp(self, scorer: MatchingScorerLike, threshold: float) -> bool:
        if self.estimation is None or self.ground_truth is None:
            return False

        score = scorer(self.estimation, self.ground_truth)
        return scorer.is_better_than(score, threshold)

    def status(self, scorer: MatchingScorerLike, threshold: float) -> MatchingStatus:
        if self.estimation is None:
            return MatchingStatus.FN
        elif self.ground_truth is None:
            return MatchingStatus.FP
        else:
            return MatchingStatus.TP if self.is_tp(scorer, threshold) else MatchingStatus.FP
