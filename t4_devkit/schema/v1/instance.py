from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .map import MapElement
from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["Instance"]


@define(slots=False)
@SCHEMAS.register(SchemaName.INSTANCE)
class Instance(SchemaBase):
    """`instance.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        category_token (str): Foreign key pointing to the category.
        instance_name (str): `<DATASET_ID>::<INSTANCE_ID>`.
        instance_index (int | None): Value of the LiDAR `instance` field (int16) for this object,
            0 to 32767.
        nbr_annotations (int): Number of annotations of this instance.
        first_annotation_token (str | None): Foreign key pointing to the first sample annotation
            or object annotation.
        last_annotation_token (str | None): Foreign key pointing to the last sample annotation
            or object annotation.
        map_element (MapElement): Link to a lanelet2 element.
    """

    category_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    instance_name: str = field(validator=validators.instance_of(str))
    instance_index: int | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(int), validators.ge(0), validators.le(2**15 - 1))
        )
    )
    nbr_annotations: int = field(validator=(validators.instance_of(int), validators.ge(0)))
    first_annotation_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    last_annotation_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    map_element: MapElement = field(
        converter=lambda x: MapElement(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(MapElement),
    )
