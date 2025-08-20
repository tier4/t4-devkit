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

        if obj.ndim == 1 and obj.shape == (9,):
            obj = obj.reshape((3, 3))

        # validate the shape of the array
        if obj.shape != (3, 3):
            raise ValueError("CameraIntrinsic must be a 3x3 array")

        return obj


class CameraDistortion(np.ndarray):
    def __new__(cls, input_array: ArrayLike) -> CameraDistortion:
        obj = np.array(input_array).view(cls)

        # validate the shape of the array
        if obj.shape != (5,):
            raise ValueError("CameraDistortion must be a 1D array of length 5")

        return obj
