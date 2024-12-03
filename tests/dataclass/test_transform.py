from __future__ import annotations

import numpy as np
from pyquaternion import Quaternion

from t4_devkit.dataclass.transform import HomogeneousMatrix


def test_tf_buffer(dummy_tf_buffer) -> None:
    # (position)
    pos1 = dummy_tf_buffer.do_transform(src="base_link", dst="base_link", position=(1, 0, 0))
    assert isinstance(pos1, np.ndarray)
    assert np.allclose(pos1, (1, 0, 0))

    # (rotation)
    rot1 = dummy_tf_buffer.do_transform(
        src="base_link",
        dst="base_link",
        rotation=(1, 0, 0, 0),
    )
    assert isinstance(rot1, Quaternion)
    assert np.allclose(rot1.rotation_matrix, np.eye(3))

    # (position, rotation)
    pos2, rot2 = dummy_tf_buffer.do_transform(
        src="base_link",
        dst="base_link",
        position=(1, 0, 0),
        rotation=(1, 0, 0, 0),
    )
    assert isinstance(pos2, np.ndarray)
    assert np.allclose(pos2, (1, 0, 0))
    assert isinstance(rot2, Quaternion)
    assert np.allclose(rot2.rotation_matrix, np.eye(3))

    # matrix
    cam2ego = HomogeneousMatrix((2, 2, 2), (1, 0, 0, 0), src="camera", dst="base_link")
    mat = dummy_tf_buffer.do_transform(src="base_link", dst="camera", matrix=cam2ego)
    assert np.allclose(
        mat.matrix,
        np.array(
            [
                [1, 0, 0, 3],
                [0, 1, 0, 3],
                [0, 0, 1, 3],
                [0, 0, 0, 1],
            ],
        ),
    )


def test_homogeneous_matrix_transform() -> None:
    ego2map = HomogeneousMatrix((1, 0, 0), (1, 0, 0, 0), src="base_link", dst="map")
    # transform(position)
    pos1_1 = ego2map.transform((1, 0, 0))
    assert np.allclose(pos1_1, np.array((2, 0, 0)))

    # transform(position=)
    pos1_2 = ego2map.transform(position=(1, 0, 0))
    assert np.allclose(pos1_2, np.array((2, 0, 0)))

    # transform(rotation)
    rot1_1 = ego2map.transform((1, 0, 0, 0))
    assert np.allclose(rot1_1.rotation_matrix, np.eye(3))

    # transform(rotation)
    rot1_2 = ego2map.transform(rotation=(1, 0, 0, 0))
    assert np.allclose(rot1_2.rotation_matrix, np.eye(3))

    # transform(position, rotation)
    pos2_1, rot2_1 = ego2map.transform((1, 0, 0), (1, 0, 0, 0))
    assert np.allclose(pos2_1, np.array((2, 0, 0)))
    assert np.allclose(rot2_1.rotation_matrix, np.eye(3))

    # transform(position=, rotation=)
    pos2_2, rot2_2 = ego2map.transform(position=(1, 0, 0), rotation=(1, 0, 0, 0))
    assert np.allclose(pos2_2, np.array((2, 0, 0)))
    assert np.allclose(rot2_2.rotation_matrix, np.eye(3))

    # transform(position, rotation=)
    pos2_3, rot2_3 = ego2map.transform((1, 0, 0), rotation=(1, 0, 0, 0))
    assert np.allclose(pos2_3, np.array((2, 0, 0)))
    assert np.allclose(rot2_3.rotation_matrix, np.eye(3))

    # transform(matrix)
    map2ego = HomogeneousMatrix((-1, 0, 0), (1, 0, 0, 0), src="map", dst="base_link")
    mat1 = ego2map.transform(map2ego)
    assert np.allclose(mat1.matrix, np.eye(4))
    assert np.allclose(mat1.position, np.zeros(3))
    assert np.allclose(mat1.rotation_matrix, np.eye(3))

    # transform(matrix=)
    mat2 = ego2map.transform(matrix=map2ego)
    assert np.allclose(mat2.matrix, np.eye(4))
    assert np.allclose(mat2.position, np.zeros(3))
    assert np.allclose(mat2.rotation_matrix, np.eye(3))


def test_homogenous_matrix_dot():
    ego2map = HomogeneousMatrix((1, 1, 1), (1, 0, 0, 0), src="base_link", dst="map")
    cam2ego = HomogeneousMatrix((2, 2, 2), (1, 0, 0, 0), src="camera", dst="base_link")
    cam2map = ego2map.dot(cam2ego)
    assert np.allclose(
        cam2map.matrix,
        np.array(
            [
                [1, 0, 0, 3],
                [0, 1, 0, 3],
                [0, 0, 1, 3],
                [0, 0, 0, 1],
            ],
        ),
    )
    assert np.allclose(cam2map.position, np.array([3, 3, 3]))  # cam position in map coords
    assert np.allclose(cam2map.rotation_matrix, np.eye(3))  # cam rotation matrix in map coords
    assert cam2map.src == "camera"
    assert cam2map.dst == "map"


def test_homogenous_matrix_inv():
    matrix = np.array(
        [
            [0.70710678, -0.70710678, 0.0, 1.0],
            [0.70710678, 0.70710678, 0.0, 2.0],
            [0.0, 0.0, 1.0, 3.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    ego2map = HomogeneousMatrix.from_matrix(matrix, src="base_link", dst="map")
    inv = ego2map.inv()
    assert np.allclose(
        inv.matrix,
        np.array(
            [
                [0.70710678, 0.70710678, 0.0, -2.12132034],
                [-0.70710678, 0.70710678, 0.0, -0.70710678],
                [0.0, 0.0, 1.0, -3.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )
    assert np.allclose(inv.position, np.array([-2.12132034, -0.70710678, -3.0]))
    assert np.allclose(
        inv.rotation_matrix,
        np.array(
            [
                [0.70710678, 0.70710678, 0.0],
                [-0.70710678, 0.70710678, 0.0],
                [0.0, 0.0, 1.0],
            ]
        ),
    )
