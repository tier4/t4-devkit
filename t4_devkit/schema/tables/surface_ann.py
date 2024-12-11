from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field

from ..name import SchemaName
from .base import SchemaBase
from .object_ann import RLEMask
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import RoiType

__all__ = ["SurfaceAnn"]


@define(slots=False)
@SCHEMAS.register(SchemaName.SURFACE_ANN)
class SurfaceAnn(SchemaBase):
    """A dataclass to represent schema table of `surface_ann.json`.

    Attributes:
        token (str): Unique record identifier.
        sample_data_token (str): Foreign key pointing to the sample data, which must be a keyframe image.
        category_token (str): Foreign key pointing to the surface category.
        mask (RLEMask): Segmentation mask using the COCO format compressed by RLE.

    Shortcuts:
    ---------
        category_name (str): Category name. This should be set after instantiated.
    """

    sample_data_token: str
    category_token: str
    mask: RLEMask = field(converter=lambda x: RLEMask(**x) if isinstance(x, dict) else x)

    # shortcuts
    category_name: str = field(init=False, factory=str)

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
