from __future__ import annotations

from typing import NewType

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pyquaternion import Quaternion

__all__ = (
    "ArrayLike",
    "NDArray",
    "NDArrayF64",
    "NDArrayI64",
    "NDArrayI32",
    "NDArrayU8",
    "NDArrayBool",
    "NDArrayStr",
    "NDArrayInt",
    "NDArrayFloat",
    "QuaternionLike",
    "TrajectoryLike",
    "CamIntrinsicLike",
    "CamDistortionLike",
    "KeypointLike",
)

# numpy
NDArrayF64 = NDArray[np.float64]
NDArrayF32 = NDArray[np.float32]
NDArrayI64 = NDArray[np.int64]
NDArrayI32 = NDArray[np.int32]
NDArrayU8 = NDArray[np.uint8]
NDArrayBool = NDArray[np.bool_]
NDArrayStr = NDArray[np.str_]

NDArrayInt = NDArrayI32 | NDArrayI64
NDArrayFloat = NDArrayF32 | NDArrayF64

# 3D
Vector2Like = NewType("Vector2Like", np.ndarray)
Vector3Like = NewType("Vector3Like", np.ndarray)
Vector6Like = NewType("Vector6Like", np.ndarray)
QuaternionLike = NewType("QuaternionLike", Quaternion)
TrajectoryLike = NewType("TrajectoryLike", np.ndarray)  # (T, 3) or (M, T, 3)
CamIntrinsicLike = NewType("CamIntrinsicLike", np.ndarray)
CamDistortionLike = NewType("CamDistortionLike", np.ndarray)

# 2D
RoiLike = NewType("RoiLike", tuple[int, int, int, int])  # (xmin, ymin, xmax, ymax)
KeypointLike = NewType("KeypointLike", np.ndarray)  # [(x0, y0), (x1, y1), ...]
