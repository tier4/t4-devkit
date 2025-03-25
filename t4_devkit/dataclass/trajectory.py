from __future__ import annotations

from typing import TYPE_CHECKING, Generator

import numpy as np
from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayFloat, NDArrayInt, QuaternionLike, Vector3Like

__all__ = ["Past", "Future"]


@define
class Trajectory:
    """A dataclass to represent trajectory.

    Attributes:
        waypoints (TrajectoryType): Waypoints matrix in the shape of (N, 3).
        confidence (float, optional): Confidence score the trajectory.

    Examples:
        >>> trajectory = Trajectory(
        ...     timestamps=[1.0, 2.0]
        ...     confidences=[1.0],
        ...     waypoints=[[[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]],
        ... )
        # Get the number of modes.
        >>> len(trajectory)
        1
        # Access the shape of waypoints matrix: (M, T, 3).
        >>> trajectory.shape
        (1, 2, 3)
        # Access waypoints as subscriptable.
        >>> trajectory[0] # for mode0
        array([[1., 1., 1.],
               [2., 2., 2.]])
        >>> trajectory[0, 0] # point0 at mode0
        array([1., 1., 1.])
        # Access confidence and waypoints for each mode as iterable.
        >>> for i, (confidence, waypoints) in trajectory:
        ...     print(f"Mode{i}: {confidence}, {waypoints}")
        ...
        Mode0: 1.0, [[1. 1. 1.] [2. 2. 2.]]
    """

    timestamps: NDArrayInt = field(converter=np.array)
    confidences: NDArrayFloat = field(converter=np.array)
    waypoints: NDArrayFloat = field(converter=np.array)

    def __attrs_post_init__(self) -> None:
        self._check_dims()

    def _check_dims(self) -> None:
        if self.waypoints.ndim != 3:
            raise ValueError(f"`waypoints` must be [M, T, D] tensor, but got {self.waypoints.ndim}")

        if self.waypoints.shape[2] != 3:
            raise ValueError(f"`waypoints` dimension must be 3, but got {self.waypoints.shape[2]}")

        # check timestamp length between timestamps and waypoints
        if len(self.timestamps) != self.waypoints.shape[1]:
            raise ValueError(
                "Timestamp length must be the same between `timestamps` and `waypoints`, "
                f"but got timestamps={len(self.timestamps)} and waypoints={self.waypoints.shape[1]}"
            )

        # check mode length between waypoints and confidences
        if self.waypoints.shape[0] != len(self.confidences):
            raise ValueError(
                "Mode length must be the same between `waypoints` and `confidences`, "
                f"but got waypoints={self.waypoints.shape[0]} and confidences={len(self.confidences)}"
            )

    def __len__(self) -> int:
        """Return the number of modes."""
        return len(self.waypoints)

    def __getitem__(self, index: int | slice[int]) -> NDArrayFloat:
        return self.waypoints[index]

    def __iter__(self) -> Generator[tuple[float, NDArrayFloat]]:
        yield from zip(self.confidences, self.waypoints, strict=True)

    @property
    def num_mode(self) -> int:
        """Return the number of trajectory modes.

        Returns:
            int: The number of trajectory modes.
        """
        return self.shape[0]

    @property
    def num_timestamp(self) -> int:
        """Return the number of timestamps.

        Returns:
            int: The number of timestamps.
        """
        return self.shape[1]

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the shape of the waypoints matrix.

        Returns:
            Shape of the matrix (M, T, D).
        """
        return self.waypoints.shape

    def translate(self, x: Vector3Like) -> None:
        """Apply a translation.

        Args:
            x (Vector3Like): 3D translation vector.
        """
        self.waypoints += x

    def rotate(self, q: QuaternionLike) -> None:
        """Apply a rotation.

        Args:
            q (QuaternionLike): Rotation quaternion.
        """
        # NOTE: R * X = X * R^T
        self.waypoints = np.dot(self.waypoints, q.rotation_matrix.T)


@define
class Past(Trajectory):
    """Represent the past trajectory features.

    Note that the expected shape of waypoints is (1, T, D)."""

    def _check_dims(self) -> None:
        super()._check_dims()

        if self.num_mode != 1:
            raise ValueError(f"The number of modes for past must be 1, but got {self.num_mode}")


@define
class Future(Trajectory):
    """Represent the future trajectory features.

    Note that the expected shape of waypoints is (M, T, D)."""
