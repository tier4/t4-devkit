from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define

from .base import BaseMetric

if TYPE_CHECKING:
    from t4_devkit.evaluation import FrameSegmentation
    from t4_devkit.typing import NDArray


class IoU(BaseMetric):
    def __init__(self) -> None:
        super().__init__()

    def __call__(self, frames: list[FrameSegmentation]) -> float:
        num_class = 1  # TODO(ktro2828)
        for frame in frames:
            intersecion_and_unions = _intersection_and_union(frame, num_class)


@define
class IntersecionAndUnion:
    intersecion: NDArray
    union: NDArray


def _intersection_and_union(
    frame: FrameSegmentation,
    k: int,
    ignore_index: int = -1,
) -> dict[str, IntersecionAndUnion]:
    output = {}
    for channel in frame.estimation.keys():
        estimation = frame.estimation[channel].reshape(-1)
        ground_truth = frame.ground_truth[channel].reshape(-1)
        estimation[ground_truth == ignore_index] = ignore_index

        intersection = estimation[estimation == ground_truth]
        e_area = np.histogram(estimation, bins=k, range=(0, k - 1))
        g_area = np.histogram(ground_truth, bins=k, range=(0, k - 1))
        union = e_area + g_area - intersection

        output[channel] = IntersecionAndUnion(intersection, union)

    return output
