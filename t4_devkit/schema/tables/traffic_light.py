from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase, impossible_empty
from .registry import SCHEMAS

__all__ = ["TrafficLight"]


@define(slots=False)
@SCHEMAS.register(SchemaName.TRAFFIC_LIGHT)
class TrafficLight(SchemaBase):
    """A dataclass to represent schema table of `traffic_light.json`.

    Attributes:
        token (str): Unique record identifier.
        instance_token (str): Foreign key pointing to the instance.
        primitive_id (str): Primitive ID of the traffic light representing.
    """

    instance_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    primitive_id: str = field(validator=(validators.instance_of(str), impossible_empty()))
