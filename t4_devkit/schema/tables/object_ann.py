from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from attrs import define, field
from pycocotools import mask as cocomask

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayU8, RoiType

__all__ = ["ObjectAnn", "RLEMask"]


@define
class RLEMask:
    """A dataclass to represent segmentation mask compressed by RLE.

    Attributes:
        size (list[int, int]): Size of image ordering (width, height).
        counts (str): RLE compressed mask data.
    """

    size: list[int, int]
    counts: str

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]

    def decode(self) -> NDArrayU8:
        """Decode segmentation mask.

        Returns:
            Decoded mask in shape of (H, W).
        """
        counts = base64.b64decode(self.counts)
        data = {"counts": counts, "size": self.size}
        return cocomask.decode(data)


@define(slots=False)
@SCHEMAS.register(SchemaName.OBJECT_ANN)
class ObjectAnn(SchemaBase):
    """A dataclass to represent schema table of `object_ann.json`.

    Attributes:
        token (str): Unique record identifier.
        sample_data_token (str): Foreign key pointing to the sample data, which must be a keyframe image.
        instance_token (str): Foreign key pointing to the instance.
        category_token (str): Foreign key pointing to the object category.
        attribute_tokens (list[str]): Foreign keys. List of attributes for this annotation.
        bbox (RoiType): Annotated bounding box. Given as [xmin, ymin, xmax, ymax].
        mask (RLEMask): Instance mask using the COCO format compressed by RLE.

    Shortcuts:
        category_name (str): Category name. This should be set after instantiated.
    """

    sample_data_token: str
    instance_token: str
    category_token: str
    attribute_tokens: list[str]
    bbox: RoiType = field(converter=tuple)
    mask: RLEMask = field(converter=lambda x: RLEMask(**x) if isinstance(x, dict) else x)

    # shortcuts
    category_name: str = field(init=False)

    @staticmethod
    def shortcuts() -> tuple[str]:
        return ("category_name",)

    @property
    def width(self) -> int:
        """Return the width of the bounding box.

        Returns:
            Bounding box width in pixel.
        """
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        """Return the height of the bounding box.

        Returns:
            Bounding box height in pixel.
        """
        return self.bbox[3] - self.bbox[1]
