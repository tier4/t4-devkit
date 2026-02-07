from __future__ import annotations

from typing import TYPE_CHECKING

from .dataset import load_dataset
from .matching import build_matcher
from .result import FrameBoxMatch

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxLike

    from .config import PerceptionEvaluationConfig
    from .dataset import EvaluationObjectLike, FrameGroundTruth


class PerceptionEvaluator:
    """Evaluation manager for perception tasks."""

    def __init__(self, config: PerceptionEvaluationConfig) -> None:
        self.config = config

        self.scene_ground_truth = load_dataset(data_root=self.config.dataset, task=self.config.task)
        self.matcher = build_matcher(params=self.config.matching)

        self.frames: list[FrameBoxMatch] = []

    def add_frame(
        self,
        unix_time: int,
        estimations: EvaluationObjectLike,
    ) -> FrameBoxMatch | None:
        """Add frame result.

        Returns None if it failed to find the closest timestamp ground truth.

        Args:
            unix_time (int): Current unix time.
            estimations (EvaluationObjectLike): Set of estimations at the current frame.

        Returns:
            Return frame result only if it succeeded to find the closest timestamp ground truth,
                otherwise None.
        """
        frame_ground_truth = self.scene_ground_truth.lookup_frame(
            unix_time=unix_time,
            tolerance=7500,
        )

        if frame_ground_truth is None:
            return None

        # TODO(ktro2828): add support of segmentation object
        if self.config.task.is_segmentation():
            raise NotImplementedError("Segmentation task is under construction.")
        else:
            frame = self._to_frame_box(
                unix_time=unix_time,
                estimations=estimations,
                frame_ground_truth=frame_ground_truth,
            )

        self.frames.append(frame)

        return frame

    def _to_frame_box(
        self,
        unix_time: int,
        estimations: list[BoxLike],
        frame_ground_truth: FrameGroundTruth,
    ) -> FrameBoxMatch:
        """Match estimations to ground truths and convert to frame result.

        Args:
            unix_time (int): Current unix time associated with estimations.
            estimations (list[BoxLike]): List of estimations.
            frame_ground_truth (FrameGroundTruth): Frame ground truth.

        Returns:
            Frame result.
        """
        matches = self.matcher(estimations, frame_ground_truth.annotations)

        return FrameBoxMatch(
            unix_time=unix_time,
            frame_index=frame_ground_truth.frame_index,
            matches=matches,
            ego2map=frame_ground_truth.ego2map,
        )
