from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pyquaternion import Quaternion

if TYPE_CHECKING:
    from t4_devkit.typing import ArrayLike, NDArray

__all__ = ["as_quaternion"]


def as_quaternion(value: ArrayLike | NDArray) -> Quaternion:
    """Convert input rotation like array to `Quaternion`.

    Args:
        value (ArrayLike | NDArray): Rotation matrix or quaternion.

    Returns:
        Quaternion: Converted instance.
    """
    return (
        Quaternion(matrix=value)
        if isinstance(value, np.ndarray) and value.ndim == 2
        else Quaternion(value)
    )
