from __future__ import annotations

from typing import TYPE_CHECKING, Generator

import numpy as np
from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.typing import TrajectoryType, TranslationType

__all__ = ["Trajectory", "to_trajectories"]


@define
class Trajectory:
    """A dataclass to represent trajectory.

    Attributes:
        waypoints (TrajectoryType): Waypoints matrix in the shape of (N, 3).
        confidence (float, optional): Confidence score the trajectory.

    Examples:
        >>> trajectory = Trajectory(
        ...     waypoints=[[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
        ...     confidence=1.0,
        ... )
        # Get the number of waypoints.
        >>> len(trajectory)
        2
        # Access the shape of waypoints matrix: (N, 3).
        >>> trajectory.shape
        (2, 3)
        # Access each point as subscriptable.
        >>> trajectory[0]
        array([1., 1., 1.])
        # Access each point as iterable.
        >>> for point in trajectory:
        ...     print(point)
        ...
        [1. 1. 1.]
        [2. 2. 2.]
    """

    waypoints: TrajectoryType = field(converter=np.asarray)
    confidence: float = field(default=1.0)

    def __attrs_post_init__(self) -> None:
        if self.waypoints.shape[1] != 3:
            raise ValueError("Trajectory dimension must be 3.")

    def __len__(self) -> int:
        return len(self.waypoints)

    def __getitem__(self, index: int) -> TranslationType:
        return self.waypoints[index]

    def __iter__(self) -> Generator[TrajectoryType]:
        yield from self.waypoints

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the shape of the waypoints matrix.

        Returns:
            Shape of the matrix (N, 3).
        """
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
