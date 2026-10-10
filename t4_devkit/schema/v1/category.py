from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["Category"]


@define(slots=False)
@SCHEMAS.register(SchemaName.CATEGORY)
class Category(SchemaBase):
    """`category.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        name (str): Category name.
        index (int | None): Value of the LiDAR `label` field for this category.
        description (str | None): Category description.
        is_thing (bool): Whether annotations of this category are individual objects with an
            instance (car, pedestrian) rather than regions without one (road, sky).
        has_orientation (bool): Whether annotations of this category may have `orientation`.
        has_number (bool): Whether annotations of this category may have `number`.
    """

    name: str = field(validator=(validators.instance_of(str), impossible_empty()))
    index: int | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(int), validators.ge(0), validators.le(255))
        )
    )
    description: str | None = field(validator=validators.optional(validators.instance_of(str)))
    is_thing: bool = field(validator=validators.instance_of(bool))
    has_orientation: bool = field(validator=validators.instance_of(bool))
    has_number: bool = field(validator=validators.instance_of(bool))
