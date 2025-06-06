from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ("Category",)


@define(slots=False)
@SCHEMAS.register(SchemaName.CATEGORY)
class Category(SchemaBase):
    """A dataclass to represent schema table of `category.json`.

    Attributes:
        token (str): Unique record identifier.
        name (str): Category name.
        description (str): Category description.
        index (int | None, optional): Category index for lidar segmentation.
    """

    name: str = field(validator=validators.instance_of(str))
    description: str = field(validator=validators.instance_of(str))
    index: int | None = field(
        default=None, validator=validators.optional(validators.instance_of(int))
    )
