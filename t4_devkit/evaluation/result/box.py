from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field

from .status import MatchingStatus

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxLike
    from t4_devkit.evaluation import MatchingScorerLike

__all__ = ["BoxMatch", "FrameBoxMatch"]


@define
class BoxMatch:
    """A class to represent the match of an estimation and ground truth.

    Raises:
        Construction raises error if both `estimation` and `ground_truth` is `None`.

    Attributes:
        estimation (BoxLike | None): Estimation.
        ground_truth (BoxLike | None): Ground truth.
    """

    estimation: BoxLike | None = field(default=None)
    ground_truth: BoxLike | None = field(default=None)

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

    def to_status(self, scorer: MatchingScorerLike, threshold: float) -> MatchingStatus:
        if self.estimation is None:
            return MatchingStatus.FN
        elif self.ground_truth is None:
            return MatchingStatus.FP
        else:
            return MatchingStatus.TP if self.is_tp(scorer, threshold) else MatchingStatus.FP


@define
class FrameBoxMatch:
    """A container of box matches at a single frame.

    Attributes:
        unix_time (int): Unix timestamp.
        frame_index (int): Index number of the frame.
        matches (list[BoxMatch]): List of box matches.
    """

    unix_time: int
    frame_index: int
    matches: list[BoxMatch]

    @property
    def num_estimation(self) -> int:
        """Return the total number of estimations."""
        return sum(m.estimation is not None for m in self.matches)

    @property
    def num_gt(self) -> int:
        """Return the total number of ground truths."""
        return sum(m.ground_truth is not None for m in self.matches)

    def num_tp(self, scorer: MatchingScorerLike, threshold: float) -> int:
        """Return the number of TPs."""
        return sum(1 for m in self.matches if m.to_status(scorer, threshold) == MatchingStatus.TP)

    def num_fp(self, scorer: MatchingScorerLike, threshold: float) -> int:
        """Return the number of FPs."""
        return sum(1 for m in self.matches if m.to_status(scorer, threshold) == MatchingStatus.FP)

    def num_fn(self, scorer: MatchingScorerLike, threshold: float) -> int:
        """Return the number of FNs."""
        return sum(1 for m in self.matches if m.to_status(scorer, threshold) == MatchingStatus.FN)

    def num_tn(self, scorer: MatchingScorerLike, threshold: float) -> int:
        """Return the number of TNs."""
        return sum(1 for m in self.matches if m.to_status(scorer, threshold) == MatchingStatus.TN)
