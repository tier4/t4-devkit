from __future__ import annotations

from typing import NewType

import numpy as np
from numpy.typing import ArrayLike, NDArray  # noqa

from .aliases import *  # noqa
from .camera import *  # noqa
from .matrix import *  # noqa
from .quaternion import *  # noqa
from .roi import *  # noqa
from .trajectory import *  # noqa
from .vector import *  # noqa

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

# 2D
# TODO(ktro2828): Implement Keypoint class and KeypointLike
KeypointLike = NewType("KeypointLike", np.ndarray)  # [(x0, y0), (x1, y1), ...]
