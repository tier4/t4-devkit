from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


class CameraIntrinsic(np.ndarray):
    """A 3x3 camera intrinsic matrix with validation.

    This class ensures that the input array is a 3x3 matrix and raises a ValueError if it is not.
    It can be constructed from a 3x3 array or 9 elements array.

    Examples:
        >>> c = CameraIntrinsic(np.eye(3))                          # OK
        >>> c = CameraIntrinsic([1, 0, 0, 0, 1, 0, 0, 0, 1])        # OK
        >>> c = CameraIntrinsic([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # OK
        >>> c = CameraIntrinsic(np.eye(2))                          # ValueError
        >>> c = CameraIntrinsic([1, 0, 0, 0, 1, 0, 0, 0])           # ValueError
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
            raise ValueError("CameraIntrinsic must be a 3x3 array")

        return obj


class CameraDistortion(np.ndarray):
    """A 1D array of length 5 representing the radial and tangential distortion coefficients.

    This class represents the distortion parameters for a camera lens, typically
    following the Brown-Conrady (or similar) model.

    The expected input is a 1D array of length 5, corresponding to the coefficients:
        - k1: Radial distortion coefficient.
        - k2: Radial distortion coefficient.
        - p1: Tangential distortion coefficient.
        - p2: Tangential distortion coefficient.
        - k3: Radial distortion coefficient.

    Examples:
        >>> c = CameraDistortion([0, 0, 0, 0, 0])                  # OK
        >>> c = CameraDistortion([1, 2, 3, 4, 5])                  # OK
        >>> c = CameraDistortion([1, 2, 3, 4])                     # ValueError
        >>> c = CameraDistortion([1, 2, 3, 4, 5, 6])               # ValueError
    """

    def __new__(cls, input_array: ArrayLike) -> CameraDistortion:
        obj = np.array(input_array).view(cls)

        # skip validation if the array is empty for non-camera
        if obj.size == 0:
            return obj

        # validate the shape of the array
        if obj.shape != (5,):
            raise ValueError("CameraDistortion must be a 1D array of length 5")

        return obj
