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


def test_view_points_with_distortion_4_params() -> None:
    """Test view_points with 4-parameter distortion model."""
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
    # 4-parameter model: [k1, k2, p1, p2]
    distortion = np.array([0.1, 0.01, 0.01, 0.01])

    project = view_points(points, intrinsic, distortion)

    # Expected result should be similar to 5-parameter case but with k3=0
    expect = np.array(
        [
            [0.541, -0.511],
            [0.541, -0.511],
            [1.0, 1.0],
        ]
    )

    assert np.allclose(project, expect, atol=1e-2)


def test_view_points_with_distortion_8_params() -> None:
    """Test view_points with 8-parameter rational distortion model."""
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
    # 8-parameter rational model: [k1, k2, p1, p2, k3, k4, k5, k6]
    distortion = np.array([0.1, 0.01, 0.01, 0.01, 0.001, 0.001, 0.001, 0.001])

    project = view_points(points, intrinsic, distortion)

    # The result should be different from basic model due to rational coefficients
    assert project.shape == (3, 2)
    assert np.all(np.isfinite(project))


def test_view_points_with_distortion_12_params() -> None:
    """Test view_points with 12-parameter distortion model (with thin prism)."""
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
    # 12-parameter model: [k1, k2, p1, p2, k3, k4, k5, k6, s1, s2, s3, s4]
    distortion = np.array(
        [0.1, 0.01, 0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.0001, 0.0001, 0.0001, 0.0001]
    )

    project = view_points(points, intrinsic, distortion)

    # The result should include thin prism distortion effects
    assert project.shape == (3, 2)
    assert np.all(np.isfinite(project))


def test_view_points_with_distortion_14_params() -> None:
    """Test view_points with 14-parameter distortion model (full model with tilted sensor)."""
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
    # 14-parameter full model: [k1, k2, p1, p2, k3, k4, k5, k6, s1, s2, s3, s4, τx, τy]
    distortion = np.array(
        [
            0.1,
            0.01,
            0.01,
            0.01,
            0.001,
            0.001,
            0.001,
            0.001,
            0.0001,
            0.0001,
            0.0001,
            0.0001,
            0.01,
            0.02,
        ]
    )

    project = view_points(points, intrinsic, distortion)

    # The result should include tilted sensor effects
    assert project.shape == (3, 2)
    assert np.all(np.isfinite(project))


def test_view_points_with_zero_distortion_all_models() -> None:
    """Test view_points with zero distortion for all parameter lengths."""
    points = np.array(
        [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
    )
    intrinsic = np.array([[1, 0, 0]])

    # Test all supported distortion parameter lengths with zero values
    distortion_models = [
        np.array([0.0, 0.0, 0.0, 0.0]),  # 4 parameters
        np.array([0.0, 0.0, 0.0, 0.0, 0.0]),  # 5 parameters
        np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),  # 8 parameters
        np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),  # 12 parameters
        np.array(
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        ),  # 14 parameters
    ]

    # Expected result without distortion
    expect = np.array(
        [
            [0.14285714, 0.25, 0.33333333],
            [0.57142857, 0.625, 0.66666667],
            [1.0, 1.0, 1.0],
        ]
    )

    for distortion in distortion_models:
        project = view_points(points, intrinsic, distortion)
        assert np.allclose(project, expect), f"Failed for {len(distortion)}-parameter model"


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
