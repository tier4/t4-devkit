from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, NewType, Sequence

import numpy as np

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType

    from .policy import MatchingPolicyLike
    from .scorer import MatchingScorerLike

ScoreTable = NewType("ScoreTable", np.ndarray[np.float64, np.bool_])


class MatchingAlgorithmImpl(ABC):
    def __init__(
        self,
        scorer: MatchingScorerLike,
        policy: MatchingPolicyLike,
        matchable_threshold: float,
    ) -> None:
        super().__init__()
        self._scorer = scorer
        self._policy = policy
        self._matchable_threshold = matchable_threshold

    def _score_table(
        self,
        estimations: Sequence[BoxType],
        ground_truths: Sequence[BoxType],
    ) -> ScoreTable:
        num_rows, num_cols = len(estimations), len(ground_truths)

        # (score, is_matchable)
        table = np.full((num_rows, num_cols, 2), fill_value=(np.nan, False))
        for i, box1 in enumerate(estimations):
            for j, box2 in enumerate(ground_truths):
                is_same_frame_id = box1.frame_id == box2.frame_id

                if not is_same_frame_id:
                    continue

                score = self._scorer(box1, box2)

                if self._scorer.is_better_than(score, self._matchable_threshold):
                    is_matchable = self._policy.is_matchable(box1, box2)
                    table[i, j] = (score, is_matchable)

        return table

    @abstractmethod
    def _do_matching(
        self,
        estimations: Sequence[BoxType],
        ground_truths: Sequence[BoxType],
        score_table: ScoreTable,
    ) -> list:  # TODO: declare a result class
        pass

    def __call__(self, estimations: Sequence[BoxType], ground_truths: Sequence[BoxType]) -> list:
        score_table = self._score_table(estimations, ground_truths)
        return self._do_matching(score_table)


class GreedyMatching(MatchingAlgorithmImpl):
    def _do_matching(
        self,
        estimations: Sequence[BoxType],
        ground_truths: Sequence[BoxType],
        score_table: ScoreTable,
    ) -> list:
        scores = score_table[..., 0]
        is_matchable = score_table[..., 1]
        masked_scores = np.where(is_matchable, scores, np.nan)

        tmp_estimations = list(deepcopy(estimations))
        tmp_ground_truths = list(deepcopy(ground_truths))

        output = []
        # 1. Matching the nearest matchable estimations and GTs
        num_estimations, *_ = score_table.shape
        for _ in range(num_estimations):
            if np.isnan(masked_scores).all():
                break

            estimation_idx, ground_truth_idx = (
                np.unravel_index(np.nanargmin(masked_scores), masked_scores.shape)
                if self._scorer.smaller_is_better()
                else np.unravel_index(np.nanargmax(masked_scores), masked_scores.shape)
            )

            estimation_picked = tmp_estimations.pop(estimation_idx)
            ground_truth_picked = tmp_ground_truths.pop(ground_truth_idx)
            # TODO: declare a result class
            output.append((estimation_picked, ground_truth_picked))

            # Remove picked estimations and GTs
            masked_scores = np.delete(masked_scores, estimation_idx, axis=0)
            masked_scores = np.delete(masked_scores, ground_truth_idx, axis=0)

            score_table = np.delete(score_table, estimation_idx, axis=0)
            score_table = np.delete(score_table, ground_truth_idx, axis=0)

        rest_scores = score_table[..., 0]
        num_rest_estimations, *_ = score_table.shape
        for _ in range(num_rest_estimations):
            if np.isnan(rest_scores).all():
                break

            estimation_idx, ground_truth_idx = (
                np.unravel_index(np.nanargmin(rest_scores), rest_scores.shape)
                if self._scorer.smaller_is_better()
                else np.unravel_index(np.nanargmax(rest_scores), rest_scores.shape)
            )

            estimation_picked = tmp_estimations.pop(estimation_idx)
            ground_truth_picked = tmp_ground_truths.pop(ground_truth_idx)
            # TODO: declare a result class
            output.append((estimation_picked, ground_truth_picked))

            rest_scores = np.delete(rest_scores, estimation_idx, axis=0)
            rest_scores = np.delete(rest_scores, ground_truth_idx, axis=1)
