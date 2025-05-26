from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field

from .base import BaseMetric

if TYPE_CHECKING:
    from t4_devkit.evaluation import BoxMatch, FrameBoxMatch, MatchingScorerLike

__all__ = ["Mota", "Motp"]


class Mota(BaseMetric):
    @define
    class ClearBuffer:
        num_gt: int = field(init=False, default=0)
        num_tp: int = field(init=False, default=0)
        num_fp: int = field(init=False, default=0)
        num_id_switch: int = field(init=False, default=0)
        score: float = field(init=False, default=0.0)

        def compute_mota(self) -> float:
            return (
                max((self.num_tp - self.num_fp - self.num_id_switch) / self.num_gt, 0.0)
                if self.num_gt > 0
                else 0.0
            )

        def compute_motp(self) -> float:
            return max(self.score / self.num_tp, 0.0) if self.num_tp > 0 else 0.0

    def __init__(self, scorer: MatchingScorerLike, threshold: float) -> None:
        self.scorer = scorer
        self.threshold = threshold

    def __call__(self, frames: list[FrameBoxMatch]) -> float:
        buffer = self._update_buffer(frames)
        return buffer.compute_mota()

    def _update_buffer(self, frames: list[FrameBoxMatch]) -> ClearBuffer:
        buffer = self.ClearBuffer()
        num_frame = len(frames)
        for i in range(1, num_frame):
            current_frame = frames[i]
            previous_frame = frames[i - 1]

            buffer.num_gt += current_frame.num_gt
            for current_match in current_frame.matches:
                is_id_switch = False
                is_same_match = False
                for previous_match in previous_frame.matches:
                    if not previous_match.is_tp(
                        self.scorer,
                        self.threshold,
                        previous_frame.ego2map,
                    ):
                        continue

                    is_id_switch = self._is_id_switched(current_match, previous_match)
                    if is_id_switch:
                        break

                    is_same_match = self._is_same_match()
                    if is_same_match:
                        buffer.num_tp += current_match.is_tp(
                            scorer=self.scorer,
                            threshold=self.threshold,
                            ego2map=current_frame.ego2map,
                        )
                        buffer.score += self.scorer(
                            previous_match.estimation,
                            previous_match.ground_truth,
                            ego2map=previous_frame.ego2map,
                        )
                        break

                if is_same_match:
                    continue

                if current_match.is_tp(self.scorer, self.threshold, current_frame.ego2map):
                    buffer.num_tp += 1
                    buffer.score += self.scorer(
                        current_match.estimation,
                        current_match.ground_truth,
                        current_frame.ego2map,
                    )
                    if is_id_switch:
                        buffer.num_id_switch += 1
                else:
                    buffer.num_fp += 1
        return buffer

    def _is_id_switched(self, current_match: BoxMatch, previous_match: BoxMatch) -> bool:
        if (not current_match.is_matched()) and (not previous_match.is_matched()):
            return False

        is_same_estimated_uuid, is_same_estimated_label, is_same_gt_uuid = self._check_match(
            current_match, previous_match
        )

        if is_same_estimated_uuid and is_same_estimated_label:
            return not is_same_gt_uuid
        else:
            return is_same_gt_uuid

    def _is_same_match(self, current_match: BoxMatch, previous_match: BoxMatch) -> bool:
        is_same_estimated_uuid, is_same_estimated_label, is_same_gt_uuid = self._check_match(
            current_match, previous_match
        )
        return is_same_estimated_uuid and is_same_estimated_label and is_same_gt_uuid

    def _check_match(
        self,
        current_match: BoxMatch,
        previous_match: BoxMatch,
    ) -> tuple[bool, bool, bool]:
        is_same_estimated_uuid = current_match.estimation.uuid == previous_match.estimation.uuid
        is_same_estimated_label = (
            current_match.estimation.semantic_label == previous_match.estimation.semantic_label
        )
        is_same_gt_uuid = current_match.ground_truth.uuid == previous_match.ground_truth.uuid

        return is_same_estimated_uuid, is_same_estimated_label, is_same_gt_uuid


class Motp(Mota):
    def __call__(self, frames: list[FrameBoxMatch]) -> float:
        buffer = self._update_buffer(frames)
        return buffer.compute_motp()
