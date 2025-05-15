from __future__ import annotations

from enum import Enum

__all__ = ["EvaluationTask"]


class EvaluationTask(str, Enum):
    """Enumeration of evaluation tasks."""

    DETECTION3D = "detection3d"
    TRACKING3D = "tracking3d"
    PREDICTION3D = "prediction3d"
    DETECTION2D = "detection2d"
    TRACKING2D = "tracking2d"

    def is_3d(self) -> bool:
        return self in (
            EvaluationTask.DETECTION3D,
            EvaluationTask.TRACKING3D,
            EvaluationTask.PREDICTION3D,
        )

    def is_2d(self) -> bool:
        return self in (EvaluationTask.DETECTION2D, EvaluationTask.TRACKING2D)
