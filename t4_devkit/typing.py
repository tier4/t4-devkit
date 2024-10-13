# flake8: noqa
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
    "TranslationType",
    "VelocityType",
    "AccelerationType",
    "RotationType",
    "VelocityType",
    "SizeType",
    "TrajectoryType",
    "CamIntrinsicType",
    "CamDistortionType",
    "RoiType",
    "KeypointType",
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
TranslationType = NewType("TranslationType", NDArrayF64)
VelocityType = NewType("VelocityType", NDArrayF64)
AccelerationType = NewType("AccelerationType", NDArrayF64)
RotationType = NewType("RotationType", Quaternion)
SizeType = NewType("SizeType", NDArrayF64)
TrajectoryType = NewType("TrajectoryType", NDArrayF64)
CamIntrinsicType = NewType("CamIntrinsicType", NDArrayF64)
CamDistortionType = NewType("CamDistortionType", NDArrayF64)

# 2D
RoiType = NewType("RoiType", tuple[int, int, int, int])  # (xmin, ymin, xmax, ymax)
KeypointType = NewType("KeypointType", NDArrayF64)
