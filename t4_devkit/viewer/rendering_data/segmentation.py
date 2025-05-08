from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import rerun as rr
from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayU8

__all__ = ["SegmentationData2D"]


@define
class SegmentationData2D:
    """A class to store 2D segmentation image data for rendering.

    Attributes:
        records (list[Record]): List of 2D segmentation mask records for rendering.
        size (tuple[int, int] | None): Size of image in the order of (height, width).
    """

    records: list[Record] = field(init=False, factory=list)
    size: tuple[int, int] | None = field(init=False, default=None)

    @define
    class Record:
        """Inner class to represent a record of 2D segmentation mask instance for rendering."""

        mask: NDArrayU8
        class_id: int
        uuid: str | None = field(default=None)

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
        if self.size is None:
            if mask.ndim != 2:
                raise ValueError("Expected the mask is 2D array (H, W).")
            self.size = mask.shape
        else:
            if self.size != mask.shape:
                raise ValueError(
                    f"All masks must be the same size. Expected: {self.size}, but got {mask.shape}."
                )

        self.records.append(self.Record(mask=mask, class_id=class_id, uuid=uuid))

    def as_segmentation_image(self) -> rr.SegmentationImage:
        """Return mask data as a `rr.SegmentationImage`.

        Returns:
            `rr.SegmentationImage` object.

        TODO:
            Add support of instance segmentation.
        """
        image = np.zeros(self.size, dtype=np.uint8)

        for record in self.records:
            image[record.mask == 1] = record.class_id

        return rr.SegmentationImage(image=image)
