from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

__all__ = ["Sample"]


@define(slots=False)
class Sample(SchemaBase):
    """`sample.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        timestamp (int): Unix time stamp [us].
        scene_token (str): Foreign key pointing to the scene.
        next (str | None): Foreign key pointing to the next sample, or None at the end of the scene.
        prev (str | None): Foreign key pointing to the previous sample, or None at the start.
    """

    timestamp: int = field(validator=validators.instance_of(int))
    scene_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    next: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    prev: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
