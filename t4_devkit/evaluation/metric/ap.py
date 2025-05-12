from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field

from ..matching import CenterDistance, HeadingYaw

if TYPE_CHECKING:
    from t4_devkit.evaluation import FrameBoxMatch

__all__ = ["Ap", "ApH"]


class Ap:
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

    def __init__(self, threshold: float) -> None:
        self.scorer = CenterDistance()
        self.threshold = threshold

    def __call__(self, frames: list[FrameBoxMatch]) -> float:
        component = self._compute_tp_fp(frames)
        return component.compute_ap()

    def _compute_tp_fp(self, frames: list[FrameBoxMatch]) -> ApBuffer:
        buffer = self.ApBuffer()
        for frame in frames:
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
                    buffer.tp_list.append(1.0)
                    buffer.fp_list.append(0.0)
                else:
                    buffer.tp_list.append(0.0)
                    buffer.fp_list.append(1.0)
        return buffer


class ApH(Ap):
    def __init__(self, threshold: float) -> None:
        super().__init__(threshold)
        self.scorer = HeadingYaw()
