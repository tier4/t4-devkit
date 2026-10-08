from __future__ import annotations

import numpy as np
import pytest

from t4_devkit.dataclass.trajectory import Future
from t4_devkit.typing import Quaternion


def test_future_trajectory(dummy_future: Future) -> None:
    """Test `Future` class including its initialization and methods."""

    assert np.allclose(dummy_future.confidences, [1.0])

    # test __len__() -> the number of modes
    assert len(dummy_future) == 1

    # test __getitem__()
    # index
    assert np.allclose(dummy_future[0], [(1.0, 1.0, 1.0), (2.0, 2.0, 2.0)])
    # slice
    assert np.allclose(dummy_future[:, 0], (1.0, 1.0, 1.0))
    assert np.allclose(dummy_future[:, 1], (2.0, 2.0, 2.0))

    # test __iter__()
    for confidence, waypoints in dummy_future:
        assert isinstance(waypoints, np.ndarray)
        assert waypoints.shape == (2, 3)
        assert isinstance(confidence, float)

    # test shape property
    assert dummy_future.num_mode == 1
    assert dummy_future.num_timestamp == 2
    assert dummy_future.shape == (1, 2, 3)


def test_trajectory_translate(dummy_future: Future) -> None:
    """Test `translate` methods of `Trajectory` class."""
    dummy_future.translate(x=(1.0, 2.0, 3.0))

    assert np.allclose(dummy_future[0, 0], (2.0, 3.0, 4.0))
    assert np.allclose(dummy_future[0, 1], (3.0, 4.0, 5.0))


def test_trajectory_rotate(dummy_future: Future) -> None:
    """Test `rotate` methods of `Trajectory` class."""
    # +90 [deg]
    dummy_future.rotate(q=Quaternion([0.7071067811865475, 0.0, 0.0, -0.7071067811865475]))

    assert np.allclose(dummy_future[0, 0], (1.0, -1.0, 1.0))
    assert np.allclose(dummy_future[0, 1], (2.0, -2.0, 2.0))


def test_to_future() -> None:
    """Test `to_trajectories` function including its valid and invalid cases."""
    # valid case
    future = Future(
        relative_timestamps=[1, 2, 3],
        confidences=[
            1.0,  # mode0
            0.5,  # mode1
        ],
        waypoints=[
            [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],  # mode0
            [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],  # mode1
        ],
    )
    assert len(future) == 2

    # invalid case: different element length
    with pytest.raises(ValueError):
        _ = Future(
            relative_timestamps=[1, 2, 3],
            confidences=[1.0],  # mode0
            waypoints=[
                [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],  # mode0
                [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],  # mode1
            ],
        )
