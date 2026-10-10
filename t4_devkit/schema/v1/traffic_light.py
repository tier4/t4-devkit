from __future__ import annotations

from enum import Enum, unique

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .annotation_type import AnnotationType

__all__ = [
    "TrafficLightColor",
    "TrafficLightShape",
    "TrafficLightStatus",
    "TrafficLightElement",
    "TrafficLight",
]


@unique
class TrafficLightColor(str, Enum):
    """Bulb color, as in Autoware TrafficLightElement."""

    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    WHITE = "white"
    UNKNOWN = "unknown"


@unique
class TrafficLightShape(str, Enum):
    """Bulb shape, as in Autoware TrafficLightElement."""

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
    UNKNOWN = "unknown"


@unique
class TrafficLightStatus(str, Enum):
    """Bulb status, as in Autoware TrafficLightElement."""

    SOLID_ON = "solid_on"
    SOLID_OFF = "solid_off"
    FLASHING = "flashing"
    UNKNOWN = "unknown"


@define
class TrafficLightElement:
    """The state of one bulb, as in Autoware TrafficLightElement.

    Attributes:
        color (TrafficLightColor): Bulb color.
        shape (TrafficLightShape): Bulb shape.
        status (TrafficLightStatus): Bulb status.
        confidence (float | None): Confidence in [0, 1].
    """

    color: TrafficLightColor = field(converter=TrafficLightColor)
    shape: TrafficLightShape = field(converter=TrafficLightShape)
    status: TrafficLightStatus = field(converter=TrafficLightStatus)
    confidence: float | None = field(
        validator=validators.optional(
            validators.and_(
                validators.instance_of((int, float)), validators.ge(0), validators.le(1)
            )
        )
    )


@define(slots=False)
class TrafficLight(SchemaBase):
    """`traffic_light.json` dataclass.

    The state of one traffic light at one time, keyed by its lanelet2 regulatory element
    (= Autoware `TrafficLightGroup.traffic_light_group_id`).

    Attributes:
        token (str): Unique record identifier.
        timestamp (int): Unix time stamp [us].
        regulatory_element_id (int): lanelet2 traffic light regulatory element ID.
        elements (list[TrafficLightElement]): Bulb states.
        object_ann_token (str | None): Foreign key pointing to the object annotation the state
            was read from.
        instance_token (str | None): Foreign key pointing to the lamp instance, for states read
            from 2D labels.
        annotation_type (AnnotationType): How the label was made.
        provenance (str | None): Vendor, recognition model and version, or "v2x".
        confidence (float | None): Confidence in [0, 1], or None for manual labels.
    """

    timestamp: int = field(validator=validators.instance_of(int))
    regulatory_element_id: int = field(validator=validators.instance_of(int))
    elements: list[TrafficLightElement] = field(
        converter=lambda x: [TrafficLightElement(**v) if isinstance(v, dict) else v for v in x],
        validator=validators.deep_iterable(
            validators.instance_of(TrafficLightElement), validators.instance_of(list)
        ),
    )
    object_ann_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    instance_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    annotation_type: AnnotationType = field(converter=AnnotationType)
    provenance: str | None = field(validator=validators.optional(validators.instance_of(str)))
    confidence: float | None = field(
        validator=validators.optional(
            validators.and_(
                validators.instance_of((int, float)), validators.ge(0), validators.le(1)
            )
        )
    )
