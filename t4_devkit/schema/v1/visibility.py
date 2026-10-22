from __future__ import annotations

from enum import Enum, unique

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase

__all__ = ["VisibilityLevel", "Visibility"]


@unique
class VisibilityLevel(str, Enum):
    """Visibility levels of an annotation.

    Attributes:
        FULL: The annotation is fully visible.
        MOST: The annotation is mostly visible, more than 50%.
        PARTIAL: The annotation is partially visible, between 10% and 50%.
        NONE: The annotation is not visible.
    """

    FULL = "full"
    MOST = "most"
    PARTIAL = "partial"
    NONE = "none"


@define(slots=False)
class Visibility(SchemaBase):
    """A dataclass to represent schema table of `visibility.json` in T4Dataset 1.0.

    Attributes:
        token (str): Unique record identifier.
        level (VisibilityLevel): Visibility level.
        description (str | None): Description of the level.
    """

    level: VisibilityLevel = field(converter=VisibilityLevel)
    description: str | None = field(validator=validators.optional(validators.instance_of(str)))
