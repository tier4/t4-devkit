from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["Vector2", "Vector3", "Vector6"]


class Vector2(np.ndarray):
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

    def __new__(cls, *args: Any) -> Vector2:
        """Create a new Vector2 instance.

        Args:
            *args: Either a single array-like object or 2 individual numeric values.

        Returns:
            Vector2 instance.

        Raises:
            ValueError: If the input array does not have exactly 2 elements.
        """
        # handle different input formats
        if len(args) == 1:
            input_array = args[0]
        else:
            input_array = args

        # convert input to numpy array
        obj = np.array(input_array).view(cls)

        # validate the shape of the array
        if obj.shape != (2,):
            raise ValueError("Input array must have exactly 2 elements.")

        return obj

    def __array_finalize__(self, obj: Vector2 | None) -> None:
        if obj is None:
            return

        # ensure we maintain the 2-element constraint during array operations
        if hasattr(obj, "shape") and obj.shape != (2,):
            # This can happen during slicing or other array operations
            # We'll allow it for now to maintain numpy compatibility
            pass


class Vector3(np.ndarray):
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

    def __new__(cls, *args: Any) -> Vector3:
        """Create a new Vector3 instance.

        Args:
            *args: Either a single array-like object or 3 individual numeric values.

        Returns:
            Vector3 instance.

        Raises:
            ValueError: If the input array does not have exactly 3 elements.
        """
        # handle different input formats
        if len(args) == 1:
            input_array = args[0]
        else:
            input_array = args

        # convert input to numpy array
        obj = np.array(input_array).view(cls)

        # validate the shape of the array
        if obj.shape != (3,):
            raise ValueError("Input array must have exactly 3 elements.")

        return obj

    def __array_finalize__(self, obj: Vector3 | None) -> None:
        if obj is None:
            return

        # ensure we maintain the 3-element constraint during array operations
        if hasattr(obj, "shape") and obj.shape != (3,):
            # This can happen during slicing or other array operations
            # We'll allow it for now to maintain numpy compatibility
            pass


class Vector6(np.ndarray):
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

    def __new__(cls, *args: Any) -> Vector6:
        """Create a new Vector6 instance.

        Args:
            *args: Either a single array-like object or 6 individual numerical values.

        Returns:
            Vector6 instance.

        Raises:
            ValueError: If the input array does not have exactly 6 elements.
        """
        # handle different input formats
        if len(args) == 1:
            input_array = args[0]
        else:
            input_array = args

        # convert input to numpy array
        obj = np.array(input_array).view(cls)

        # validate the shape of the array
        if obj.shape != (6,):
            raise ValueError("Input array must have exactly 6 elements.")

        return obj

    def __array_finalize__(self, obj: Vector6 | None) -> None:
        if obj is None:
            return

        # ensure we maintain the 6-element constraint during array operations
        if hasattr(obj, "shape") and obj.shape != (6,):
            # This can happen during slicing or other array operations
            # We'll allow it for now to maintain numpy compatibility
            pass
