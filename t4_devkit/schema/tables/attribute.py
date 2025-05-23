from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ["Attribute"]


@define(slots=False)
@SCHEMAS.register(SchemaName.ATTRIBUTE)
class Attribute(SchemaBase):
    """A dataclass to represent schema table of `attribute.json`.

    Attributes:
        token (str): Unique record identifier.
        name (str): Attribute name.
        description (str): Attribute description.
    """

    name: str = field(validator=validators.instance_of(str))
    description: str = field(validator=validators.instance_of(str))
