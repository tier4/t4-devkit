from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ["Sample"]


@define(slots=False)
@SCHEMAS.register(SchemaName.SAMPLE)
class Sample(SchemaBase):
    """A dataclass to represent schema table of `sample.json`.

    Attributes:
        token (str): Unique record identifier.
        timestamp (int): Unix time stamp.
        scene_token (str): Foreign key pointing to the scene.
        next (str): Foreign key pointing the sample that follows this in time. Empty if end of scene.
        prev (str): Foreign key pointing the sample that precedes this in time. Empty if start of scene.

    Shortcuts:
    ---------
        data (dict[str, str]): Sensor channel and its token.
            This should be set after instantiated.
        ann_3ds (list[str]): List of foreign keys pointing the sample annotations.
            This should be set after instantiated.
        ann_2ds (list[str]): List of foreign keys pointing the object annotations.
            This should be set after instantiated.
        surface_anns (list[str]): List of foreign keys pointing the surface annotations.
            This should be set after instantiated.
    """

    timestamp: int = field(validator=validators.instance_of(int))
    scene_token: str = field(validator=validators.instance_of(str))
    next: str = field(validator=validators.instance_of(str))  # noqa: A003
    prev: str = field(validator=validators.instance_of(str))

    # shortcuts
    data: dict[str, str] = field(factory=dict, init=False)
    ann_3ds: list[str] = field(factory=list, init=False)
    ann_2ds: list[str] = field(factory=list, init=False)
    surface_anns: list[str] = field(factory=list, init=False)
