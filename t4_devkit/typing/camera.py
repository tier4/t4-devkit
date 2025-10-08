from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


class CameraIntrinsic(np.ndarray):
    """A 3x3 camera intrinsic matrix with validation.

    This class ensures that the input array is a 3x3 matrix and raises a ValueError if it is not.
    It can be constructed from a 3x3 array or 9 elements array.

    Note that for non-camera, the array can be empty.

    Examples:
        >>> i = CameraIntrinsic(np.eye(3))                          # OK
        >>> i = CameraIntrinsic([1, 0, 0, 0, 1, 0, 0, 0, 1])        # OK
        >>> i = CameraIntrinsic([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # OK
        >>> i = CameraIntrinsic([])                                 # OK
        >>> i = CameraIntrinsic(np.eye(2))                          # ValueError
        >>> i = CameraIntrinsic([1, 0, 0, 0, 1, 0, 0, 0])           # ValueError
    """

    def __new__(cls, input_array: ArrayLike) -> CameraIntrinsic:
        obj = np.array(input_array).view(cls)

        # skip validation if the array is empty for non-camera
        if obj.size == 0:
            return obj

        if obj.ndim == 1 and obj.shape == (9,):
            obj = obj.reshape((3, 3))

        # validate the shape of the array
        if obj.shape != (3, 3):
            raise ValueError(f"CameraIntrinsic must be a 3x3 array, got: {obj.shape}")

        return obj


class CameraDistortion(np.ndarray):
    """A 1D array representing camera lens distortion coefficients.

    This class represents the distortion parameters for a camera lens following
    the OpenCV distortion model. It supports arrays of length 4, 5, 8, 12, or 14
    elements, corresponding to different distortion models.

    The distortion coefficients follow the OpenCV convention:
    (k1, k2, p1, p2[, k3[, k4, k5, k6[, s1, s2, s3, s4[, τx, τy]]]])

    Coefficient meanings:
        - k1, k2, k3, k4, k5, k6: Radial distortion coefficients
        - p1, p2: Tangential distortion coefficients  
        - s1, s2, s3, s4: Thin prism distortion coefficients
        - τx, τy: Tilted sensor distortion coefficients

    Supported array lengths:
        - 4 elements: (k1, k2, p1, p2) - Basic radial and tangential
        - 5 elements: (k1, k2, p1, p2, k3) - Extended radial distortion
        - 8 elements: (k1, k2, p1, p2, k3, k4, k5, k6) - Rational model
        - 12 elements: (k1, k2, p1, p2, k3, k4, k5, k6, s1, s2, s3, s4) - With thin prism
        - 14 elements: (k1, k2, p1, p2, k3, k4, k5, k6, s1, s2, s3, s4, τx, τy) - Full model

    Note that for non-camera, the array can be empty.

    Examples:
        >>> d = CameraDistortion([0, 0, 0, 0])                     # 4 elements: basic model
        >>> d = CameraDistortion([0, 0, 0, 0, 0])                  # 5 elements: with k3
        >>> d = CameraDistortion([1, 2, 3, 4, 5])                  # 5 elements: valid coefficients
        >>> d = CameraDistortion([1, 2, 3, 4, 5, 6, 7, 8])         # 8 elements: rational model
        >>> d = CameraDistortion([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])  # 12 elements: with thin prism
        >>> d = CameraDistortion([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])  # 14 elements: full model
        >>> d = CameraDistortion([])                               # Empty array for non-camera
        >>> d = CameraDistortion([1, 2, 3])                        # ValueError: invalid length
        >>> d = CameraDistortion([1, 2, 3, 4, 5, 6])               # ValueError: invalid length
    """

    def __new__(cls, input_array: ArrayLike) -> CameraDistortion:
        obj = np.array(input_array).view(cls)

        # skip validation if the array is empty for non-camera
        if obj.size == 0:
            return obj

        # validate the shape of the array
        # OpenCV supports distortion coefficient arrays of length 4, 5, 8, 12, or 14
        valid_lengths = (4, 5, 8, 12, 14)
        if obj.ndim != 1 or obj.shape[0] not in valid_lengths:
            raise ValueError(f"CameraDistortion must be a 1D array of length {valid_lengths}, got: {obj.shape}")

        return obj
