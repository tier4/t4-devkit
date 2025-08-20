from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["Vector2", "Vector3", "Vector6"]


class BaseVector(np.ndarray):
    """Base class for fixed-size numpy vector arrays with validation."""

    _expected_shape: tuple[int, ...] = ()

    def __new__(cls, *args: Any):
        """Create a new BaseVector instance."""
        if len(args) == 1:
            input_array = args[0]
        else:
            input_array = args

        # convert input to numpy array
        obj = np.array(input_array).view(cls)

        # validate the shape of the array
        if obj.shape != cls._expected_shape:
            raise ValueError(f"Input array must have exactly {cls._expected_shape[0]} elements")

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        # Allow shape mismatch for numpy compatibility (e.g., slicing)
        if hasattr(obj, "shape") and obj.shape != self._expected_shape:
            pass


class Vector2(BaseVector):
    """A 2-element numpy array with validation.

    This class ensures that the array always has exactly 2 elements.
    It can be constructed from any array-like object that can be converted
    to a 2-element numpy array.

    Examples:
        >>> v = Vector2([1, 2])             # OK
        >>> v = Vector2(np.array([1, 2]))   # OK
        >>> v = Vector2(1, 2)               # OK
        >>> v = Vector2([1, 2, 3])          # ValueError
    """

    _expected_shape = (2,)


class Vector3(BaseVector):
    """A 3-element numpy array with validation.

    This class ensures that the array always has exactly 3 elements.
    It can be constructed from any array-like object that can be converted
    to a 3-element numpy array.

    Examples:
        >>> v = Vector3([1, 2, 3])              # OK
        >>> v = Vector3(np.array([1, 2, 3]))    # OK
        >>> v = Vector3(1, 2, 3)                # OK
        >>> v = Vector3([1, 2])                 # ValueError
    """

    _expected_shape = (3,)


class Vector6(BaseVector):
    """A 6-element numpy array with validation.

    This class ensures that the array always has exactly 6 elements.
    It can be constructed from any array-like object that can be converted
    to a 6-element numpy array.

    Examples:
        >>> v = Vector6([1, 2, 3, 4, 5, 6])             # OK
        >>> v = Vector6(np.array([1, 2, 3, 4, 5, 6]))   # OK
        >>> v = Vector6(1, 2, 3, 4, 5, 6)               # OK
        >>> v = Vector6([1, 2])                         # ValueError
    """

    _expected_shape = (6,)
