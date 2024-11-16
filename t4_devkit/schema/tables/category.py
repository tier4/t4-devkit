from __future__ import annotations

from attrs import define

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
    """

    name: str
    description: str
