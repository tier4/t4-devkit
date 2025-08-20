"""Type aliases for common input patterns in the T4 dataset toolkit.

This module provides convenient type aliases that allow functions to accept
various input formats while maintaining type safety and documentation clarity.

Example:
    Instead of writing:
        def my_function(position: Union[Vector3, ArrayLike, Sequence[float], tuple[float, float, float], list[float]]):

    You can simply write:
        def my_function(position: Vector3Like):

The aliases support the most common input patterns found in robotics and computer vision:
- Native T4 types (Vector3, Quaternion, etc.)
- NumPy arrays and array-like objects
- Python sequences (lists, tuples)
- Nested sequences for matrices and trajectories
"""

from __future__ import annotations

from typing import Sequence, Union

import numpy as np
from numpy.typing import ArrayLike

from .camera import CameraDistortion, CameraIntrinsic
from .matrix import Matrix3x3, Matrix4x4
from .quaternion import Quaternion
from .roi import Roi
from .vector import Vector2, Vector3, Vector6

__all__ = [
    # Vector aliases
    "Vector2Like",
    "Vector3Like",
    "Vector6Like",
    # Rotation aliases
    "QuaternionLike",
    "RotationLike",
    # Geometric aliases
    "RoiLike",
    "PointLike",
    "PointsLike",
    # Matrix aliases
    "Matrix3x3Like",
    "Matrix4x4Like",
    # Trajectory aliases
    "TrajectoryLike",
    # Camera parameter aliases
    "CameraIntrinsicLike",
    "CameraDistortionLike",
    # Numeric aliases
    "ScalarLike",
]

# =============================================================================
# Vector type aliases
# =============================================================================

Vector2Like = Union[
    Vector2,  # Native Vector2 type
    ArrayLike,  # NumPy array-like
    Sequence[float],  # Generic sequence
    tuple[float, float],  # Exact 2-tuple
    list[float],  # List of floats
]
"""Type alias for 2D vector inputs.

Accepts:
    - Vector2 instances
    - NumPy arrays with shape (2,)
    - Lists: [x, y]
    - Tuples: (x, y)
    - Any sequence with 2 float elements
"""

Vector3Like = Union[
    Vector3,  # Native Vector3 type
    ArrayLike,  # NumPy array-like
    Sequence[float],  # Generic sequence
    tuple[float, float, float],  # Exact 3-tuple
    list[float],  # List of floats
]
"""Type alias for 3D vector inputs.

Accepts:
    - Vector3 instances
    - NumPy arrays with shape (3,)
    - Lists: [x, y, z]
    - Tuples: (x, y, z)
    - Any sequence with 3 float elements
"""

Vector6Like = Union[
    Vector6,  # Native Vector6 type
    ArrayLike,  # NumPy array-like
    Sequence[float],  # Generic sequence
    tuple[float, ...],  # Variable-length tuple
    list[float],  # List of floats
]
"""Type alias for 6D vector inputs.

Accepts:
    - Vector6 instances
    - NumPy arrays with shape (6,)
    - Lists: [x1, x2, x3, x4, x5, x6]
    - Tuples: (x1, x2, x3, x4, x5, x6)
    - Any sequence with 6 float elements
"""

# =============================================================================
# Rotation type aliases
# =============================================================================

QuaternionLike = Union[
    Quaternion,  # Native Quaternion type
    ArrayLike,  # NumPy array-like
    Sequence[float],  # Generic sequence
    tuple[float, float, float, float],  # Exact 4-tuple (w, x, y, z)
    list[float],  # List of floats
]
"""Type alias for quaternion inputs.

Accepts:
    - Quaternion instances
    - NumPy arrays with shape (4,) - [w, x, y, z]
    - Lists: [w, x, y, z]
    - Tuples: (w, x, y, z)
    - Any sequence with 4 float elements representing quaternion components
"""

RotationLike = Union[
    QuaternionLike,  # Quaternion representations
    ArrayLike,  # NumPy array (could be rotation matrix)
]
"""Type alias for general rotation inputs.

Accepts:
    - All QuaternionLike inputs
    - 3x3 rotation matrices as NumPy arrays
    - Any array-like object representing rotations
"""

# =============================================================================
# Geometric type aliases
# =============================================================================

RoiLike = Union[
    Roi,  # Native Roi type
    ArrayLike,  # NumPy array-like
    Sequence[float],  # Generic sequence
    tuple[float, float, float, float],  # Exact 4-tuple (xmin, ymin, xmax, ymax)
    list[float],  # List of floats
]
"""Type alias for Region of Interest (ROI) inputs.

Accepts:
    - Roi instances
    - NumPy arrays with shape (4,)
    - Lists: [xmin, ymin, xmax, ymax]
    - Tuples: (xmin, ymin, xmax, ymax)
    - Any sequence with 4 float elements representing bounding box coordinates
"""

PointLike = Union[
    Vector2Like,  # 2D point
    Vector3Like,  # 3D point
]
"""Type alias for single point inputs (2D or 3D)."""

PointsLike = Union[
    ArrayLike,  # NumPy array-like
    Sequence[Sequence[float]],  # Nested sequences
    list[list[float]],  # List of lists
    list[tuple[float, ...]],  # List of tuples
]
"""Type alias for multiple points inputs.

Accepts:
    - NumPy arrays with shape (N, 2) or (N, 3)
    - Lists of lists: [[x1, y1], [x2, y2], ...]
    - Lists of tuples: [(x1, y1), (x2, y2), ...]
    - Any nested sequence representing multiple points
"""

# =============================================================================
# Matrix type aliases
# =============================================================================

Matrix3x3Like = Union[
    Matrix3x3,  # Native Matrix3x3
    ArrayLike,  # NumPy array-like
    Sequence[Sequence[float]],  # Nested sequences
    list[list[float]],  # 3x3 list of lists
]
"""Type alias for 3x3 matrix inputs.

Accepts:
    - NumPy arrays with shape (3, 3)
    - Nested lists: [[a, b, c], [d, e, f], [g, h, i]]
    - Any nested sequence representing a 3x3 matrix
"""

Matrix4x4Like = Union[
    Matrix4x4,  # Native Matrix4x4
    ArrayLike,  # NumPy array-like
    Sequence[Sequence[float]],  # Nested sequences
    list[list[float]],  # 4x4 list of lists
]
"""Type alias for 4x4 matrix inputs.

Accepts:
    - NumPy arrays with shape (4, 4)
    - Nested lists: 4x4 structure
    - Any nested sequence representing a 4x4 matrix
"""


# =============================================================================
# Trajectory type aliases
# =============================================================================

TrajectoryLike = Union[
    ArrayLike,  # NumPy array-like
    Sequence[Sequence[Sequence[float]]],  # Triple-nested sequences
    list[list[list[float]]],  # List of lists of lists
]
"""Type alias for trajectory inputs.

Accepts:
    - NumPy arrays with shape (M, T, D) where:
      - M = number of modes
      - T = number of timesteps
      - D = spatial dimensions (usually 3)
    - Triple-nested sequences with same structure
"""

# =============================================================================
# Camera parameter type aliases
# =============================================================================

CameraIntrinsicLike = Union[
    CameraIntrinsic,  # Native CameraIntrinsic
    ArrayLike,  # NumPy array-like
    Sequence[Sequence[float]],  # Nested sequences
    list[list[float]],  # List of lists of lists
]
"""Type alias for camera parameter inputs.

Accepts:
    - CameraIntrinsic instances
    - NumPy arrays with shape (3, 3)
    - Nested sequences of float values
"""

CameraDistortionLike = Union[
    CameraDistortion,  # Native CameraDistortion
    ArrayLike,  # NumPy array-like
    Sequence[float],  # Sequences
    list[float],  # List of lists of lists
]
"""Type alias for camera distortion inputs.

Accepts:
    - CameraDistortion instances
    - NumPy arrays with shape (5,)
    - Sequence of float values
"""

# =============================================================================
# Numeric type aliases
# =============================================================================

ScalarLike = Union[
    int,  # Integer
    float,  # Float
    np.number,  # NumPy scalar types
]
"""Type alias for scalar numeric inputs.

Accepts:
    - Python int or float
    - NumPy scalar types
"""
