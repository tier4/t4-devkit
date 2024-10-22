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
    estimation: BoxType
    ground_truth: BoxType | None = field(default=None)

    def is_label_correct(self) -> bool:
        return (
            False
            if self.ground_truth is None
            else self.estimation.semantic_label == self.ground_truth.semantic_label
        )

    def is_correct(self, scorer: MatchingScorerLike, threshold: float) -> bool:
        return scorer.is_better_than(self.score, threshold)

    def status(self, scorer: MatchingScorerLike, threshold: float) -> MatchingStatus:
        if self.ground_truth is None:
            return MatchingStatus.FN
        else:
            score = scorer(self.estimation, self.ground_truth)
            return (
                MatchingStatus.TP if scorer.is_better_than(score, threshold) else MatchingStatus.FP
            )
