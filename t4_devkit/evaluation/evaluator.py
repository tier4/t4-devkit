from __future__ import annotations

from typing import TYPE_CHECKING

from .dataset import load_dataset
from .matching import build_matcher
from .result import FrameBoxMatch, FrameSegmentation

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxLike
    from t4_devkit.typing import NDArray

    from .config import PerceptionEvaluationConfig
    from .dataset import EvaluationObjectLike, FrameGroundTruth


class PerceptionEvaluator:
    """Evaluation manager for perception tasks."""

    def __init__(self, config: PerceptionEvaluationConfig) -> None:
        self.config = config

        self.scene_ground_truth = load_dataset(data_root=self.config.dataset, task=self.config.task)
        self.matcher = build_matcher(params=self.config.matching)

        self.frames: list[FrameBoxMatch | FrameSegmentation] = []

    def add_frame(
        self,
        unix_time: int,
        estimations: EvaluationObjectLike,
    ) -> FrameBoxMatch | FrameSegmentation | None:
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

        if self.config.task.is_segmentation():
            # 2D/3D segmentation
            if isinstance(estimations, list):
                raise TypeError("Expected NDArray or dict[str, NDArray], but got list")

            frame = self._to_frame_segmentation(
                unix_time=unix_time,
                estimations=estimations,
                frame_ground_truth=frame_ground_truth,
            )
        else:
            # 2D/3D detection, tracking, prediction
            if not isinstance(estimations, list):
                raise TypeError(f"Expected list[BoxLike] objects, but got {type(estimations)}")

            frame = self._to_frame_box(
                unix_time=unix_time,
                estimations=estimations,
                frame_ground_truth=frame_ground_truth,
            )

        self.frames.append(frame)

        return frame

    def _to_frame_segmentation(
        self,
        unix_time: int,
        estimations: NDArray | dict[str, NDArray],
        frame_ground_truth: FrameGroundTruth,
    ) -> FrameSegmentation:
        """Match estimations to ground truths and convert to frame result.

        Args:
            unix_time (int): Current unix time associated with estimations.
            estimations (NDArray | dict[str, NDArray]): Estimation.
            frame_ground_truth (FrameGroundTruth): Frame ground truth.

        Returns:
            Frame result.
        """
        if isinstance(frame_ground_truth.annotations, list):
            raise TypeError("Expected NDArray or dict[str, NDArray], but got list")

        return FrameSegmentation(
            unix_time=unix_time,
            frame_index=frame_ground_truth.frame_index,
            estimation=estimations,
            ground_truth=frame_ground_truth.annotations,
        )

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
