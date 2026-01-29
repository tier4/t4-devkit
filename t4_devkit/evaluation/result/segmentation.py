from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define

if TYPE_CHECKING:
    from t4_devkit.typing import NDArray

__all__ = ["FrameSegmentation"]


@define
class FrameSegmentation:
    """A container of 2D/3D estimated and ground truth segmentation labels."""

    unix_time: int
    frame_index: int
    estimation: NDArray | dict[str, NDArray]
    ground_truth: NDArray | dict[str, NDArray]

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.estimation, type(self.ground_truth)):
            raise TypeError(
                "Estimation and ground truth must be of the same type, "
                f"got estimation: {type(self.estimation)} and ground truth: {type(self.ground_truth)}"
            )

        def _check_ndim(arr: NDArray, ndim: int, prefix: str):
            if arr.ndim != ndim:
                raise ValueError(f"{prefix} array must have {ndim} dimensions, got {arr.ndim}")

        if isinstance(self.estimation, dict) and isinstance(self.ground_truth, dict):
            for key, value in self.estimation.items():
                _check_ndim(value, 2, f"Estimation for {key}")
            for key, value in self.ground_truth.items():
                _check_ndim(value, 2, f"Ground truth for {key}")
        elif isinstance(self.estimation, np.ndarray) and isinstance(self.ground_truth, np.ndarray):
            _check_ndim(self.estimation, 1, "Estimation")
            _check_ndim(self.ground_truth, 1, "Ground truth")
        else:
            raise TypeError(
                "Estimation and ground truth must be either both arrays or both dictionaries, "
                f"got estimation: {type(self.estimation)} and ground truth: {type(self.ground_truth)}"
            )
