from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from typing_extensions import Self

from ..name import SchemaName
from .base import SchemaBase
from .object_ann import RLEMask
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import RoiType

__all__ = ("SurfaceAnn",)


@dataclass
@SCHEMAS.register(SchemaName.SURFACE_ANN)
class SurfaceAnn(SchemaBase):
    """A dataclass to represent schema table of `surface_ann.json`.

    Attributes:
        token (str): Unique record identifier.
        sample_data_token (str): Foreign key pointing to the sample data, which must be a keyframe image.
        category_token (str): Foreign key pointing to the surface category.
        mask (RLEMask): Segmentation mask using the COCO format compressed by RLE.
    """

    token: str
    sample_data_token: str
    category_token: str
    mask: RLEMask

    # shortcuts
    category_name: str = field(init=False)

    @staticmethod
    def shortcuts() -> tuple[str]:
        return ("category_name",)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        new_data = data.copy()
        new_data["mask"] = RLEMask(**data["mask"])
        return cls(**new_data)

    @property
    def bbox(self) -> RoiType:
        """Return a bounding box corners calculated from polygon vertices.

        Returns:
            Given as [xmin, ymin, xmax, ymax].
        """
        mask = self.mask.decode()
        indices = np.where(mask == 1)
        xmin, ymin = np.min(indices, axis=1)
        xmax, ymax = np.max(indices, axis=1)
        return xmin, ymin, xmax, ymax
