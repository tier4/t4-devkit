from __future__ import annotations

import numpy as np


def is_vector3(instance, attribute, value) -> None:
    """Validate if the input value is 3D vector."""
    if not isinstance(value, np.ndarray) or value.shape != (3,):
        raise ValueError(f"{attribute.name} must be 3D vector: {value}")


def is_vector6(instance, attribute, value) -> None:
    """Validate if the input value is 6D vector."""
    if not isinstance(value, np.ndarray) or value.shape != (6,):
        raise ValueError(f"{attribute.name} must be 6D vector: {value}")


def is_roi(instance, attribute, value) -> None:
    """Validate if the input value is RoI."""
    if len(value) != 4:
        raise ValueError(f"{attribute.name} must be (xmin, ymin, xmax, ymax): {value}")

    xmin, ymin, xmax, ymax = value
    if (xmax < xmin) or (ymax < ymin):
        raise ValueError(
            f"{attribute.name} must be (xmin, ymin, xmax, ymax) and xmin <= xmax && ymin <= ymax: {value}"
        )


def is_trajectory(instance, attribute, value) -> None:
    """Validate if the input value is trajectory."""
    if not isinstance(value, np.ndarray) or value.ndim != 3 or value.shape[2] != 3:
        raise ValueError(f"{attribute.name} must be the shape of (M, T, 3): {value}")
