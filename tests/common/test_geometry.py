import numpy as np

from t4_devkit.common.geometry import is_box_in_image, view_points
from t4_devkit.schema import VisibilityLevel


def test_view_points_by_perspective_projection() -> None:
    points = np.array(
        [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
    )
    intrinsic = np.array([[1, 0, 0]])

    project = view_points(points, intrinsic)

    expect = np.array(
        [
            [0.14285714, 0.25, 0.33333333],
            [0.57142857, 0.625, 0.66666667],
            [1.0, 1.0, 1.0],
        ]
    )

    assert np.allclose(project, expect)


def test_view_points_by_orthographic_projection() -> None:
    points = np.array(
        [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
    )
    intrinsic = np.array([[1, 0, 0], [0, 1, 0]])

    project = view_points(points, intrinsic, normalize=False)

    expect = np.array(
        [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
    )

    assert np.allclose(project, expect)


def test_view_points_with_distortion() -> None:
    points = np.array(
        [
            [0.5, -0.5],
            [0.5, -0.5],
            [1, 1],
        ]
    )
    intrinsic = np.array(
        [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ]
    )
    distortion = np.array([0.1, 0.01, 0.01, 0.01, 0.001])

    project = view_points(points, intrinsic, distortion)

    expect = np.array(
        [
            [0.5413125, -0.5113125],
            [0.5413125, -0.5113125],
            [1.0, 1.0],
        ]
    )

    assert np.allclose(project, expect)


# TODO(ktro2828): add unit testing for VisibilityLevel.FULL


def test_box_partial_visible(dummy_box3d, dummy_camera_calibration) -> None:
    """Test `is_box_in_image` function in the case of the box is partially visible."""
    img_size, intrinsic = dummy_camera_calibration

    dummy_box3d.position = (0.0, 0.0, 2.0)
    assert is_box_in_image(
        dummy_box3d,
        intrinsic=intrinsic,
        img_size=img_size,
        visibility=VisibilityLevel.PARTIAL,
    )


def test_box_not_visible(dummy_box3d, dummy_camera_calibration) -> None:
    """Test `is_box_in_image` function in the case of the box is not visible."""
    img_size, intrinsic = dummy_camera_calibration

    dummy_box3d.position = (100.0, 100.0, 1.0)
    assert not is_box_in_image(
        dummy_box3d,
        intrinsic=intrinsic,
        img_size=img_size,
        visibility=VisibilityLevel.PARTIAL,
    )


def test_box_behind_camera(dummy_box3d, dummy_camera_calibration) -> None:
    """Test `is_box_in_image` function in the case of the box is behind of the camera."""

    img_size, intrinsic = dummy_camera_calibration

    dummy_box3d.position = (100.0, 100.0, -1.0)
    assert not is_box_in_image(
        dummy_box3d,
        intrinsic=intrinsic,
        img_size=img_size,
        visibility=VisibilityLevel.FULL,
    )
