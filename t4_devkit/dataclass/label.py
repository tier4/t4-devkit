from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum, auto, unique
from typing import TypeVar

from typing_extensions import Self

__all__ = [
    "LabelPrefix",
    "ObjectLabel",
    "TrafficLightLabel",
    "LabelType",
    "SemanticLabel",
    "convert_label",
]


@unique
class LabelPrefix(Enum):  # TODO: LabelKind is better
    OBJECT = auto()
    TRAFFIC_LIGHT = auto()

    @classmethod
    def from_name(cls, name: str) -> Self:
        name = name.upper()
        assert name in cls.__members__, f"Unexpected label prefix: {name}"
        return cls.__members__[name]


@unique
class BaseLabel(Enum):
    """Abstract base enum of label elements."""

    @classmethod
    def from_name(cls, name: str) -> Self:
        name = name.upper()
        assert name in cls.__members__, f"Unexpected label name: {name}"
        return cls.__members__[name]

    def __eq__(self, other: Self | str) -> bool:
        return self.value == other.upper() if isinstance(other, str) else self == other


@unique
class ObjectLabel(BaseLabel):
    """An enum to represent a label of an traffic participant object."""

    UNKNOWN = auto()
    CAR = auto()
    TRUCK = auto()
    BUS = auto()
    BICYCLE = auto()
    MOTORBIKE = auto()
    PEDESTRIAN = auto()
    ANIMAL = auto()


@unique
class TrafficLightLabel(BaseLabel):
    """An enum to represent a label of a traffic light."""

    UNKNOWN = auto()
    GREEN = auto()
    GREEN_STRAIGHT = auto()
    GREEN_LEFT = auto()
    GREEN_RIGHT = auto()
    YELLOW = auto()
    YELLOW_STRAIGHT = auto()
    YELLOW_LEFT = auto()
    YELLOW_RIGHT = auto()
    YELLOW_STRAIGHT_LEFT = auto()
    YELLOW_STRAIGHT_RIGHT = auto()
    YELLOW_STRAIGHT_LEFT_RIGHT = auto()
    RED = auto()
    RED_STRAIGHT = auto()
    RED_LEFT = auto()
    RED_RIGHT = auto()
    RED_STRAIGHT_LEFT = auto()
    RED_STRAIGHT_RIGHT = auto()
    RED_STRAIGHT_LEFT_RIGHT = auto()
    RED_LEFT_DIAGONAL = auto()
    RED_RIGHT_DIAGONAL = auto()


# type aliases
LabelType = TypeVar("LabelType", bound=BaseLabel)


@dataclass(frozen=True, eq=False)
class SemanticLabel:
    label: LabelType
    original: str
    attributes: list[str] = field(default_factory=list)

    def __eq__(self, other: Self) -> bool:
        return self.label == other.label


# =====================
# Label conversion
# =====================

# Name mapping (key: value) = (original: expected in Label enum)
DEFAULT_NAME_MAPPING: dict[str, str] = {
    # === ObjectLabel ===
    # CAR
    "car": "CAR",
    "vehicle.car": "CAR",
    "vehicle.construction": "CAR",
    "vehicle.emergency (ambulance & police)": "CAR",
    "vehicle.police": "CAR",
    # TRUCK
    "truck": "TRUCK",
    "vehicle.truck": "TRUCK",
    "trailer": "TRUCK",
    "vehicle.trailer": "TRUCK",
    # BUS
    "bus": "BUS",
    "vehicle.bus": "BUS",
    "vehicle.bus (bendy & rigid)": "BUS",
    # BICYCLE
    "bicycle": "BICYCLE",
    "vehicle.bicycle": "BICYCLE",
    # MOTORBIKE
    "motorbike": "MOTORBIKE",
    "vehicle.motorbike": "MOTORBIKE",
    "motorcycle": "MOTORBIKE",
    "vehicle.motorcycle": "MOTORBIKE",
    # PEDESTRIAN
    "pedestrian": "PEDESTRIAN",
    "pedestrian.child": "PEDESTRIAN",
    "pedestrian.personal_mobility": "PEDESTRIAN",
    "pedestrian.police_officer": "PEDESTRIAN",
    "pedestrian.stroller": "PEDESTRIAN",
    "pedestrian.wheelchair": "PEDESTRIAN",
    "construction_worker": "PEDESTRIAN",
    # ANIMAL
    "animal": "ANIMAL",
    # UNKNOWN
    "movable_object.barrier": "UNKNOWN",
    "movable_object.debris": "UNKNOWN",
    "movable_object.pushable_pullable": "UNKNOWN",
    "movable_object.trafficcone": "UNKNOWN",
    "movable_object.traffic_cone": "UNKNOWN",
    "static_object.bicycle_lack": "UNKNOWN",
    "static_object.bollard": "UNKNOWN",
    "forklift": "UNKNOWN",
    # === TrafficLightLabel ===
    # GREEN
    "green": "GREEN",
    "green_straight": "GREEN_STRAIGHT",
    "green_left": "GREEN_LEFT",
    "green_right": "GREEN_RIGHT",
    # YELLOW
    "yellow": "YELLOW",
    "yellow_straight": "YELLOW_STRAIGHT",
    "yellow_left": "YELLOW_LEFT",
    "yellow_right": "YELLOW_RIGHT",
    "yellow_straight_left": "YELLOW_STRAIGHT_LEFT",
    "yellow_straight_right": "YELLOW_STRAIGHT_RIGHT",
    "yellow_straight_left_right": "YELLOW_STRAIGHT_LEFT_RIGHT",
    # RED
    "red": "RED",
    "red_straight": "RED_STRAIGHT",
    "red_left": "RED_LEFT",
    "red_right": "RED_RIGHT",
    "red_straight_left": "RED_STRAIGHT_LEFT",
    "red_straight_right": "RED_STRAIGHT_RIGHT",
    "red_straight_left_right": "RED_STRAIGHT_LEFT_RIGHT",
    "red_straight_left_diagonal": "RED_LEFT_DIAGONAL",
    "red_straight_leftdiagonal": "RED_LEFT_DIAGONAL",
    "red_straight_right_diagonal": "RED_RIGHT_DIAGONAL",
    "red_straight_rightdiagonal": "RED_RIGHT_DIAGONAL",
    # CROSSWALK
    "crosswalk_red": "RED",
    "crosswalk_green": "GREEN",
    "crosswalk_unknown": "UNKNOWN",
}


def convert_label(
    prefix: str | LabelPrefix,
    original: str,
    attributes: list[str] | None = None,
    name_mapping: dict[str, str] | None = None,
    *,
    update_default_mapping: bool = False,
) -> SemanticLabel:
    """Covert string original label name to `SemanticLabel` object.

    Args:
        prefix (str | LabelPrefix): Prefix of label defined in `LabelPrefix`.
        original (str): Original label name. For example, `vehicle.car`.
        attributes (list[str] | None, optional): List of label attributes.
        name_mapping (dict[str, str] | None, optional): Name mapping for original and label.
            If `None`, `DEFAULT_NAME_MAPPING` will be used.
        update_default_mapping (bool, optional): Whether to update `DEFAULT_NAME_MAPPING` by
            `name_mapping`. If `False` and `name_mapping` is specified,
            the specified `name_mapping` is used instead of `DEFAULT_NAME_MAPPING` completely.
            Note that, this parameter works only if `name_mapping` is specified.

    Returns:
        Converted `SemanticLabel` object.
    """
    if isinstance(prefix, str):
        prefix = LabelPrefix.from_name(prefix)

    # set name mapping
    if name_mapping is None:
        name_mapping = DEFAULT_NAME_MAPPING
    elif update_default_mapping:
        name_mapping.update(DEFAULT_NAME_MAPPING)

    # convert original to name for Label object
    if original in name_mapping:
        name = name_mapping[original]
    else:
        warnings.warn(f"{name} is not included in mapping, use UNKNOWN.", stacklevel=1)
        name = "UNKNOWN"

    if prefix == LabelPrefix.OBJECT:
        label = ObjectLabel.from_name(name)
    elif prefix == LabelPrefix.TRAFFIC_LIGHT:
        label = TrafficLightLabel.from_name(name)

    return (
        SemanticLabel(label, original)
        if attributes is None
        else SemanticLabel(label, original, attributes)
    )