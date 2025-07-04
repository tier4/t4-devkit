from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pyquaternion import Quaternion

if TYPE_CHECKING:
    from t4_devkit.typing import ArrayLike, NDArray

__all__ = ["to_quaternion"]


def to_quaternion(x: ArrayLike | NDArray) -> Quaternion:
    """Convert input rotation like array to `Quaternion`.

    Args:
        x (ArrayLike | NDArray): Rotation matrix or quaternion.

    Returns:
        Quaternion: Converted instance.
    """
    return (
        Quaternion(matrix=x)
        if isinstance(x, np.ndarray) and x.ndim == 2
        else Quaternion(x)
    )
