import numpy as np
import pytest

from t4_devkit.dataclass.trajectory import Trajectory, to_trajectories


def test_trajectory() -> None:
    """Test `Trajectory` class including its initialization and methods."""
    # list item is converted to NDArray internally
    trajectory = Trajectory(
        waypoints=[[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
        confidence=1.0,
    )

    assert trajectory.confidence == 1.0

    # test __len__()
    assert len(trajectory) == 2

    # test __getitem__()
    assert np.allclose(trajectory[0], [1.0, 1.0, 1.0])
    assert np.allclose(trajectory[1], [2.0, 2.0, 2.0])

    # test shape property
    assert trajectory.shape == (2, 3)


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
