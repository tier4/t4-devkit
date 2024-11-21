from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import rerun as rr

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayU8

__all__ = ["SegmentationData2D"]


class SegmentationData2D:
    """A class to store 2D segmentation image data for rendering."""

    def __init__(self) -> None:
        self._masks: list[NDArrayU8] = []
        self._class_ids: list[int] = []
        self._uuids: list[str | None] = []

        self._size: tuple[int, int] = None  # (height, width)

    def append(self, mask: NDArrayU8, class_id: int, uuid: str | None = None) -> None:
        """Append a segmentation mask and its class ID.

        Args:
            mask (NDArrayU8): Mask image, in the shape of (H, W).
            class_id (int): Class ID.
            uuid (str | None, optional): Unique instance identifier.

        Raises:
            ValueError:
                - Expecting all masks are 2D array (H, W).
                - Expecting all masks are the same shape (H, W).
        """
        if self._size is None:
            if mask.ndim != 2:
                raise ValueError("Expected the mask is 2D array (H, W).")
            self._size = mask.shape
        else:
            if self._size != mask.shape:
                raise ValueError(
                    f"All masks must be the same size. Expected: {self._size}, "
                    f"but got {mask.shape}."
                )
        self._masks.append(mask)
        self._class_ids.append(class_id)
        self._uuids.append(uuid)

    def as_segmentation_image(self) -> rr.SegmentationImage:
        """Return mask data as a `rr.SegmentationImage`.

        Returns:
            `rr.SegmentationImage` object.

        TODO:
            Add support of instance segmentation.
        """
        image = np.zeros(self._size, dtype=np.uint8)

        for mask, class_id in zip(self._masks, self._class_ids, strict=True):
            image[mask == 1] = class_id

        return rr.SegmentationImage(image=image)
