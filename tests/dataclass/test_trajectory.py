import numpy as np
import pytest
from pyquaternion import Quaternion

from t4_devkit.dataclass.trajectory import to_trajectories


def test_trajectory(dummy_trajectory) -> None:
    """Test `Trajectory` class including its initialization and methods."""

    assert dummy_trajectory.confidence == 1.0

    # test __len__()
    assert len(dummy_trajectory) == 2

    # test __getitem__()
    assert np.allclose(dummy_trajectory[0], (1.0, 1.0, 1.0))
    assert np.allclose(dummy_trajectory[1], (2.0, 2.0, 2.0))

    # test __iter__()
    for point in dummy_trajectory:
        assert isinstance(point, np.ndarray)
        assert point.shape == (3,)

    # test shape property
    assert dummy_trajectory.shape == (2, 3)


def test_trajectory_translate(dummy_trajectory) -> None:
    """Test `translate` methods of `Trajectory` class."""
    dummy_trajectory.translate(x=(1.0, 2.0, 3.0))

    assert np.allclose(dummy_trajectory[0], (2.0, 3.0, 4.0))
    assert np.allclose(dummy_trajectory[1], (3.0, 4.0, 5.0))


def test_trajectory_rotate(dummy_trajectory) -> None:
    """Test `rotate` methods of `Trajectory` class."""
    # +90 [deg]
    dummy_trajectory.rotate(q=Quaternion([0.7071067811865475, 0.0, 0.0, -0.7071067811865475]))

    assert np.allclose(dummy_trajectory[0], (1.0, -1.0, 1.0))
    assert np.allclose(dummy_trajectory[1], (2.0, -2.0, 2.0))


def test_to_trajectories() -> None:
    """Test `to_trajectories` function including its valid and invalid cases."""
    # valid case
    trajectories = to_trajectories(
        waypoints=[
            [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],  # mode0
            [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],  # mode1
        ],
        confidences=[
            1.0,  # mode0
            2.0,  # mode1
        ],
    )
    assert len(trajectories) == 2

    # invalid case: different element length
    with pytest.raises(ValueError):
        _ = to_trajectories(
            waypoints=[
                [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],
                [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]],
            ],
            confidences=[1.0],
        )
