from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from t4_devkit.typing import TrajectoryType, TranslationType

__all__ = ["Trajectory", "to_trajectories"]


@dataclass
class Trajectory:
    waypoints: TrajectoryType
    confidence: float

    def __post_init__(self) -> None:
        if not isinstance(self.waypoints, np.ndarray):
            self.waypoints = np.array(self.waypoints)

    def __len__(self) -> int:
        return len(self.waypoints)

    def __getitem__(self, index: int) -> TranslationType:
        return self.waypoints[index]

    @property
    def shape(self) -> tuple[int, ...]:
        return self.waypoints.shape


def to_trajectories(
    waypoints: list[TrajectoryType],
    confidences: list[float],
) -> list[Trajectory]:
    """Convert a list of waypoints and confidences to a list of `Trajectory`s for each mode.

    Args:
        waypoints (list[TrajectoryType]): List of waypoints for each mode.
        confidences (list[float]): List of confidences for each mode.

    Returns:
        List of `Trajectory`s for each mode.
    """
    return [
        Trajectory(points, confidence)
        for points, confidence in zip(waypoints, confidences, strict=True)
    ]
