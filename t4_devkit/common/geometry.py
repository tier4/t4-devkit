from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from t4_devkit.schema import VisibilityLevel

if TYPE_CHECKING:
    from t4_devkit.dataclass import Box3D
    from t4_devkit.typing import CameraDistortionLike, CameraIntrinsicLike, NDArrayF64


__all__ = ("view_points", "is_box_in_image")


def view_points(
    points: NDArrayF64,
    intrinsic: CameraIntrinsicLike,
    distortion: CameraDistortionLike | None = None,
    *,
    normalize: bool = True,
) -> NDArrayF64:
    """Project 3d points on a 2d plane. It can be used to implement both perspective and orthographic projections.

    It first applies the dot product between the points and the view.

    Args:
        points (NDArrayF64): Matrix of points, which is the shape of (3, n) and (x, y, z) is along each column.
        intrinsic (CameraIntrinsicLike): nxn camera intrinsic matrix (n <= 4).
        distortion (CameraDistortionLike | None, optional): Camera distortion coefficients, which is the shape of (n,) where n can be 4, 5, 8, 12, or 14.
        normalize (bool, optional): Whether to normalize the remaining coordinate (along the 3rd axis).

    Returns:
        Projected points in the shape of (3, n). If `normalize=False`, the 3rd coordinate is the height.
    """
    assert intrinsic.shape[0] <= 4
    assert intrinsic.shape[1] <= 4
    assert points.shape[0] == 3

    viewpad = np.eye(4)
    viewpad[: intrinsic.shape[0], : intrinsic.shape[1]] = intrinsic

    nbr_points = points.shape[1]

    points = np.concatenate((points, np.ones((1, nbr_points))))

    if distortion is not None:
        assert distortion.shape[0] >= 4
        D = distortion
        # distortion is [k1, k2, p1, p2, k3, k4, k5, k6, s1, s2, s3, s4, τx, τy]. 
        # Undistortion implementation from: https://docs.opencv.org/3.4/da/d54/group__imgproc__transform.html#ga7dfb72c9cf9780a347fbe3d1c47e5d5a
        while len(D) < 14:
            D = np.insert(D, len(D), 0)
        k1, k2, p1, p2, k3, k4, k5, k6, s1, s2, s3, s4, tau_x, tau_y = D

        x_ = points[0]
        y_ = points[1]
        r2 = x_**2 + y_**2
        f1 = (1 + k1 * r2 + k2 * r2**2 + k3 * r2**3) / (1 + k4 * r2 + k5 * r2**2 + k6 * r2**3)
        f2 = x_ * y_
        x__ = x_ * f1 + 2 * p1 * f2 + p2 * (r2 + 2 * x_**2) + s1 * r2 + s2 * r2**2
        y__ = y_ * f1 + p1 * (r2 + 2 * y_**2) + 2 * p2 * f2 + s3 * r2 + s4 * r2**2
        
        # Apply tilted sensor distortion (τx, τy)
        if tau_x != 0 or tau_y != 0:
            # Rotation matrix R(tau_x, tau_y)
            R = np.array([
                [np.cos(tau_y), 0, -np.sin(tau_y)],
                [np.sin(tau_x) * np.sin(tau_y), np.cos(tau_x), np.sin(tau_x) * np.cos(tau_y)],
                [np.cos(tau_x) * np.sin(tau_y), -np.sin(tau_x), np.cos(tau_x) * np.cos(tau_y)]
            ])

            # Extract required elements
            R13, R23, R33 = R[0, 2], R[1, 2], R[2, 2]

            # Build M matrix
            M = np.array([
                [R33, 0, -R13],
                [0, R33, -R23],
                [0, 0, 1]
            ])

            # Homogeneous coordinates
            points_3d = np.vstack([x__, y__, np.ones_like(x__)])

            # Apply the tilt transform
            tilted = M @ (R @ points_3d)

            # Normalize
            x__ = tilted[0] / tilted[2]
            y__ = tilted[1] / tilted[2]
        
        u = viewpad[0, 0] * x__ + viewpad[0, 2]
        v = viewpad[1, 1] * y__ + viewpad[1, 2]
        points = np.stack([u, v, points[2, :]], axis=0)
    else:
        points = np.dot(viewpad, points)
        points = points[:3, :]

    if normalize:
        points /= points[2:3, :]

    return points


def is_box_in_image(
    box: Box3D,
    intrinsic: CameraIntrinsicLike,
    img_size: tuple[int, int],
    visibility: VisibilityLevel = VisibilityLevel.NONE,
) -> bool:
    """Check if a box is visible inside of an image without considering its occlusions.

    Args:
        box (Box3D): The box to be checked.
        intrinsic (CameraIntrinsicLike): 3x3 camera intrinsic matrix.
        img_size (tuple[int, int]): Image size in the order of (width, height).
        visibility (VisibilityLevel, optional): Enum member of VisibilityLevel.

    Returns:
        Return True if visibility condition is satisfied.
    """
    corners_3d = box.corners().T  # (3, 8)
    corners_on_img = view_points(corners_3d, intrinsic, normalize=True)[:2, :]

    img_w, img_h = img_size
    is_visible = np.logical_and(corners_on_img[0, :] >= 0, corners_on_img[0, :] <= img_w)
    is_visible = np.logical_and(is_visible, corners_on_img[1, :] <= img_h)
    is_visible = np.logical_and(is_visible, corners_on_img[1, :] >= 0)
    is_visible = np.logical_and(is_visible, corners_3d[2, :] > 1)

    in_front = corners_3d[2, :] > 0.1  # True if a corner is at least 0.1 meter in front of camera.

    if visibility == VisibilityLevel.FULL:
        return np.all(is_visible) and np.all(in_front)
    elif visibility in (VisibilityLevel.MOST, VisibilityLevel.PARTIAL):
        return np.any(is_visible)
    elif visibility == VisibilityLevel.NONE:
        return True
    else:
        raise ValueError(f"Unexpected visibility: {visibility}")
