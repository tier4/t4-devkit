from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pycocotools import mask as cocomask
from typing_extensions import Self

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import NDArrayU8, RoiType

__all__ = ("ObjectAnn", "RLEMask")


@dataclass
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
        return cocomask.decode(data).T


@dataclass
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
    """

    token: str
    sample_data_token: str
    instance_token: str
    category_token: str
    attribute_tokens: list[str]
    bbox: RoiType
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
