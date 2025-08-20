from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

__all__ = ["Matrix3x3", "Matrix4x4"]


class Matrix3x3(np.ndarray):
    """A 3x3 matrix with validation.

    Examples:
        >>> matrix = Matrix3x3([[1, 2, 3], [4, 5, 6], [7, 8, 9]])   # OK
        >>> matrix = Matrix3x3(np.eye(3))                           # OK
        >>> matrix = Matrix3x3([[1, 2], [4, 5], [7, 8]])            # ValueError
        >>> matrix = Matrix3x3(np.eye(2))                           # ValueError
    """

    def __new__(cls, input_array: ArrayLike) -> Matrix3x3:
        obj = np.array(input_array).view(cls)
        if obj.shape != (3, 3):
            raise ValueError(f"Input array must be of shape (3, 3), got: {obj.shape}")
        return obj


class Matrix4x4(np.ndarray):
    """A 4x4 matrix with validation.

    Examples:
        >>> matrix = Matrix4x4([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]) # OK
        >>> matrix = Matrix4x4(np.eye(4))                                                       # OK
        >>> matrix = Matrix4x4([[1, 2], [4, 5], [7, 8]])                                        # ValueError
        >>> matrix = Matrix4x4(np.eye(2))                                                       # ValueError
    """

    def __new__(cls, input_array: ArrayLike) -> Matrix4x4:
        obj = np.array(input_array).view(cls)
        if obj.shape != (4, 4):
            raise ValueError(f"Input array must be of shape (4, 4), got: {obj.shape}")
        return obj
