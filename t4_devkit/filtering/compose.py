from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .functional import (
    FilterByDistance,
    FilterByLabel,
    FilterByNumPoints,
    FilterByPosition,
    FilterBySpeed,
    FilterByUUID,
)
from .parameter import FilterParams

if TYPE_CHECKING:
    from t4_devkit.dataclass import BoxType, TransformBuffer

    from .functional import BoxFilterFunction


class BoxFilter:
    """A class composes multiple filtering functions."""

    def __init__(self, params: FilterParams, tf_buffer: TransformBuffer) -> None:
        """Construct a new object.

        Args:
            params (FilterParams): Filtering parameters.
            tf_buffer (TransformBuffer): Transformation buffer.
        """
        self.filters: list[BoxFilterFunction] = [
            FilterByLabel.from_params(params),
            FilterByUUID.from_params(params),
            FilterByDistance.from_params(params),
            FilterByPosition.from_params(params),
            FilterBySpeed.from_params(params),
            FilterByNumPoints.from_params(params),
        ]

        self.tf_buffer = tf_buffer

    def __call__(self, boxes: Sequence[BoxType]) -> list[BoxType]:
        output: list[BoxType] = []

        for box in boxes:
            tf_matrix = self.tf_buffer.lookup_transform(box.frame_id, "base_link")

            is_ok = all(func(box, tf_matrix) for func in self.filters)

            if is_ok:
                output.append(box)

        return output
