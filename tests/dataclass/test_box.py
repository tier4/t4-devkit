import math

import numpy as np
from pyquaternion import Quaternion

from t4_devkit.dataclass import distance_box


def test_box3d(dummy_box3d) -> None:
    """Test `Box3D` class.

    Args:
        dummy_box3d (Box3D): 3D box.
    """
    # test properties
    assert np.allclose(dummy_box3d.size, (1.0, 1.0, 1.0))
    assert dummy_box3d.area == 1.0
    assert dummy_box3d.volume == 1.0

    assert np.allclose(
        dummy_box3d.corners(box_scale=1.0),
        np.array(
            [
                [1.5, 1.5, 1.5],
                [1.5, 0.5, 1.5],
                [1.5, 0.5, 0.5],
                [1.5, 1.5, 0.5],
                [0.5, 1.5, 1.5],
                [0.5, 0.5, 1.5],
                [0.5, 0.5, 0.5],
                [0.5, 1.5, 0.5],
            ],
        ),
    )


def test_box3d_translate(dummy_box3d) -> None:
    dummy_box3d.translate(x=(1.0, 2.0, 3.0))

    assert np.allclose(dummy_box3d.position, (2.0, 3.0, 4.0))


def test_box3d_rotate(dummy_box3d) -> None:
    # +90 [deg]
    dummy_box3d.rotate(q=Quaternion([0.7071067811865475, 0.0, 0.0, -0.7071067811865475]))

    assert np.allclose(dummy_box3d.position, (1.0, -1.0, 1.0))
    assert np.allclose(
        dummy_box3d.rotation.rotation_matrix,
        np.array(
            [
                [0, 1, 0],
                [-1, 0, 0],
                [0, 0, 1],
            ]
        ),
    )


def test_box2d(dummy_box2d) -> None:
    """Test `Box2D` class.

    Args:
        dummy_box2d (Box2D): 2D box.
    """
    # test properties
    assert dummy_box2d.offset == (100, 100)
    assert dummy_box2d.size == (50, 50)
    assert dummy_box2d.width == 50
    assert dummy_box2d.height == 50
    assert dummy_box2d.center == (125, 125)
    assert dummy_box2d.area == 2500


def test_distance_box(dummy_box3d, dummy_tf_buffer) -> None:
    """Test `distance_box` function.

    Args:
        dummy_box3d (Box3D): 3D box.
        dummy_tf_buffer (TransformBuffer): Transformation buffer.
    """
    tf_matrix = dummy_tf_buffer.lookup_transform(dummy_box3d.frame_id, "base_link")
    distance = distance_box(dummy_box3d, tf_matrix)

    assert math.isclose(distance, np.linalg.norm([1.0, 1.0, 1.0]))
