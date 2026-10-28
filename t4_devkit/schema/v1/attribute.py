from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase

from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["Attribute"]


@define(slots=False)
@SCHEMAS.register(SchemaName.ATTRIBUTE)
class Attribute(SchemaBase):
    """`attribute.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        name (str): Attribute name.
        description (str | None): Attribute description.
    """

    name: str = field(validator=validators.instance_of(str))
    description: str | None = field(validator=validators.optional(validators.instance_of(str)))
