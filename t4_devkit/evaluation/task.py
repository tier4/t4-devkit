from __future__ import annotations

from enum import Enum, unique

__all__ = ["EvaluationTask"]


@unique
class EvaluationTask(str, Enum):
    """Enumeration of evaluation tasks."""

    DETECTION3D = "detection3d"
    TRACKING3D = "tracking3d"
    PREDICTION3D = "prediction3d"
    SEGMENTATION3D = "segmentation3d"
    DETECTION2D = "detection2d"
    TRACKING2D = "tracking2d"
    SEGMENTATION2D = "segmentation2d"

    def is_3d(self) -> bool:
        """Indicate whether the task considers 3D objects.

        Returns:
            Return `True` if the task is in [detection3d, tracking3d, prediction3d, segmentation3d].
        """
        return self in (
            EvaluationTask.DETECTION3D,
            EvaluationTask.TRACKING3D,
            EvaluationTask.PREDICTION3D,
            EvaluationTask.SEGMENTATION3D,
        )

    def is_2d(self) -> bool:
        """Indicate whether the task considers 2D objects.

        Returns:
            Return `True` if the task is in [detection2d, tracking2d, segmentation2d].
        """
        return self in (
            EvaluationTask.DETECTION2D,
            EvaluationTask.TRACKING2D,
            EvaluationTask.SEGMENTATION2D,
        )

    def is_segmentation(self) -> bool:
        """Indicate whether the task deals with segmentation.

        Returns:
            Return `True` if the task is in [segmentation3d, segmentation2d].
        """
        return self in (EvaluationTask.SEGMENTATION3D, EvaluationTask.SEGMENTATION2D)
