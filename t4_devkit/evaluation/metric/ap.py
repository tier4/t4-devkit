from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field

from .base import BaseMetric

if TYPE_CHECKING:
    from t4_devkit.evaluation import BoxMatch, FrameBoxMatch, MatchingScorerLike

__all__ = ["Ap", "ApH"]


class Ap(BaseMetric):
    num_recall_point = 101
    min_precision = 0.1
    min_recall = 0.1

    @define
    class ApBuffer:
        """Buffer to compute AP."""

        num_gt: int = field(init=False, default=0)
        tp_list: list[float] = field(init=False, factory=list)
        fp_list: list[float] = field(init=False, factory=list)
        confidences: list[float] = field(init=False, factory=list)

        def compute_ap(self) -> float:
            """Compute average precision."""
            if self.num_gt == 0:
                return 0.0

            sorted_idx = np.argsort(self.confidences)[::-1]
            tp_sorted = np.array(self.tp_list)[sorted_idx]
            fp_sorted = np.array(self.fp_list)[sorted_idx]

            tps = np.cumsum(tp_sorted)
            fps = np.cumsum(fp_sorted)

            precisions = []
            recalls = []
            for tp, fp in zip(tps, fps, strict=True):
                denominator = tp + fp
                precisions.append(0.0) if denominator == 0.0 else precisions.append(
                    tp / denominator
                )
                recalls.append(tp / self.num_gt)

            precision_envelope = np.maximum.accumulate(precisions[::-1])[::-1]

            recall_interp = np.linspace(0.0, 1.0, Ap.num_recall_point)

            precision_interp = np.interp(recall_interp, recalls, precision_envelope, right=0)

            first_idx = int(round(100 * Ap.min_recall))

            filtered_precision = precision_interp[first_idx:] - Ap.min_precision
            filtered_precision = np.clip(filtered_precision, 0.0, None)

            return float(np.mean(filtered_precision)) / (1.0 - Ap.min_precision)

    def __init__(self, scorer: MatchingScorerLike, threshold: float) -> None:
        self.scorer = scorer
        self.threshold = threshold

    def __call__(self, frames: list[FrameBoxMatch]) -> float:
        buffer = self._update_buffer(frames)
        return buffer.compute_ap()

    def _compute_tp(self, box_match: BoxMatch) -> float:
        return 1.0

    def _update_buffer(self, frames: list[FrameBoxMatch]) -> ApBuffer:
        buffer = self.ApBuffer()
        for frame in frames:
            self._update_buffer_frame(frame, buffer)
        return buffer

    def _update_buffer_frame(self, frame: FrameBoxMatch, buffer: ApBuffer) -> None:
        buffer.num_gt += frame.num_gt
        for box_match in frame.matches:
            if box_match.estimation is None:
                continue

            buffer.confidences.append(box_match.estimation.confidence)
            if box_match.is_tp(
                scorer=self.scorer,
                threshold=self.threshold,
                ego2map=frame.ego2map,
            ):
                buffer.tp_list.append(self._compute_tp(box_match))
                buffer.fp_list.append(0.0)
            else:
                buffer.tp_list.append(0.0)
                buffer.fp_list.append(1.0)


class ApH(Ap):
    def __init__(self, scorer: MatchingScorerLike, threshold: float) -> None:
        super().__init__(scorer=scorer, threshold=threshold)

    def _compute_tp(self, box_match: BoxMatch) -> float:
        if not box_match.is_matched():
            return 0.0

        diff_yaw = box_match.estimation.diff_yaw(box_match.ground_truth)
        if diff_yaw > np.pi:
            diff_yaw = 2.0 * np.pi - diff_yaw
        return min(1.0, max(0.0, 1.0 - diff_yaw / np.pi))
