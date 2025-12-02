from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase, impossible_empty
from .registry import SCHEMAS

__all__ = ["Instance"]


@define(slots=False)
@SCHEMAS.register(SchemaName.INSTANCE)
class Instance(SchemaBase):
    """A dataclass to represent schema table of `instance.json`.

    Attributes:
        token (str): Unique record identifier.
        category_token (str): Foreign key pointing to the object category.
        instance_name (str): Dataset name and instance ID defined in annotation tool.
        nbr_annotations (int): Number of annotations of this instance.
        first_annotation_token (str): Foreign key pointing to the first annotation of this instance.
            Empty if the dataset only contains 2D annotations.
        last_annotation_token (str): Foreign key pointing to the last annotation of this instance.
            Empty if the dataset only contains 2D annotations.
    """

    category_token: str = field(validator=(validators.instance_of(str), impossible_empty))
    instance_name: str = field(validator=validators.instance_of(str))
    nbr_annotations: int = field(validator=validators.instance_of(int))
    first_annotation_token: str = field(validator=validators.instance_of(str))
    last_annotation_token: str = field(validator=validators.instance_of(str))
