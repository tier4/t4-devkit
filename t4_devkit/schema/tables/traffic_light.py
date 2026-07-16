from __future__ import annotations

from enum import Enum, unique

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase, impossible_empty
from .registry import SCHEMAS

__all__ = [
    "TrafficLight",
    "TrafficLightElement",
    "TrafficLightElementColor",
    "TrafficLightElementShape",
]


@unique
class TrafficLightElementColor(str, Enum):
    UNKNOWN = "unknown"
    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    WHITE = "white"


@unique
class TrafficLightElementShape(str, Enum):
    UNKNOWN = "unknown"
    CIRCLE = "circle"
    LEFT_ARROW = "left_arrow"
    RIGHT_ARROW = "right_arrow"
    UP_ARROW = "up_arrow"
    UP_LEFT_ARROW = "up_left_arrow"
    UP_RIGHT_ARROW = "up_right_arrow"
    DOWN_ARROW = "down_arrow"
    DOWN_LEFT_ARROW = "down_left_arrow"
    DOWN_RIGHT_ARROW = "down_right_arrow"
    CROSS = "cross"


@define
class TrafficLightElement:
    color: TrafficLightElementColor = field(converter=TrafficLightElementColor)
    shape: TrafficLightElementShape = field(converter=TrafficLightElementShape)

    @staticmethod
    def to_traffic_light_element(x: dict | TrafficLightElement) -> TrafficLightElement:
        if isinstance(x, TrafficLightElement):
            return x
        return TrafficLightElement(**x)


@define(slots=False)
@SCHEMAS.register(SchemaName.TRAFFIC_LIGHT)
class TrafficLight(SchemaBase):
    """A dataclass to represent schema table of ``traffic_light.json``.

    Attributes:
        token (str): The token of the traffic light.
        sample_token (str): Foreign key pointing the sample.
        lane_connector_id (str): The lane connector ID of the traffic light.
        elements (list[TrafficLightElement]): List of the traffic light elements.
    """

    sample_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    lane_connector_id: str = field(validator=(validators.instance_of(str), impossible_empty()))
    elements: list[TrafficLightElement] = field(
        converter=lambda x: [TrafficLightElement.to_traffic_light_element(s) for s in x],
        validator=impossible_empty(),
    )
