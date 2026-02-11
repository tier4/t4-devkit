from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define

if TYPE_CHECKING:
    from t4_devkit.typing import NDArray

__all__ = ["FrameSegmentation"]


@define
class FrameSegmentation:
    """A container of 2D/3D estimated and ground truth segmentation labels."""

    unix_time: int
    frame_index: int
    estimation: dict[str, NDArray]
    ground_truth: dict[str, NDArray]

    def __attrs_post_init__(self) -> None:
        if isinstance(self.estimation, dict) and isinstance(self.ground_truth, dict):
            for e_key, e_value in self.estimation.items():
                if e_key not in self.ground_truth:
                    raise KeyError(f"{e_key} not in ground truth")

                g_value = self.ground_truth[e_key]
                if e_value.ndim != g_value.ndim:
                    raise ValueError(
                        "Array dimensions must be the same, "
                        f"estimation: {e_value.ndim}, ground truth: {g_value.ndim}"
                    )
