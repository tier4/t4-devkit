from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from typing_extensions import Self

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if sys.version_info < (3, 11):
    from enum import Enum

    class StrEnum(str, Enum):
        pass
else:
    from enum import StrEnum

__all__ = (
    "VehicleState",
    "ShiftState",
    "IndicatorState",
    "Indicators",
    "AdditionalInfo",
)


class ShiftState(StrEnum):
    PARK = "PARK"
    REVERSE = "REVERSE"
    NEUTRAL = "NEUTRAL"
    HIGH = "HIGH"
    FORWARD = "FORWARD"
    LOW = "LOW"
    NONE = "NONE"


class IndicatorState(StrEnum):
    ON = "on"
    OFF = "off"


@dataclass
class Indicators:
    """A dataclass to represent state of each indicator.

    Attributes:
        left (IndicatorState | None): State of the left indicator.
        right (IndicatorState | None): State of the right indicator.
        hazard (IndicatorState | None): State of the hazard lights.
    """

    left: IndicatorState | None = field(default=None)
    right: IndicatorState | None = field(default=None)
    hazard: IndicatorState | None = field(default=None)


@dataclass
class AdditionalInfo:
    """A dataclass to represent additional vehicle state information.

    Attributes:
        speed (float | None): Speed of the vehicle [km/h].
    """

    speed: float | None = field(default=None)


@dataclass
@SCHEMAS.register(SchemaName.VEHICLE_STATE)
class VehicleState(SchemaBase):
    """A dataclass to represent schema table of `vehicle_state.json`.

    Attributes:
        token (str): Unique record identifier.
        timestamp (int): Unix time stamp.
        accel_pedal (float | None): Accel pedal position [%].
        brake_pedal (float | None): Brake pedal position [%].
        steer_pedal (float | None): Steering wheel position [%].
        steering_tire_angle (float | None): Steering tire angle [rad].
        steering_wheel_angle (float | None): Steering wheel angle [rad].
        shift_state (ShiftState | None): Shift state.
        indicators (Indicators | None): State of the each indicator.
        additional_info (AdditionalInfo | None): Additional vehicle state information.
    """

    token: str
    timestamp: int
    accel_pedal: float | None = field(default=None)
    brake_pedal: float | None = field(default=None)
    steer_pedal: float | None = field(default=None)
    steering_tire_angle: float | None = field(default=None)
    steering_wheel_angle: float | None = field(default=None)
    shift_state: ShiftState | None = field(default=None)
    indicators: Indicators | None = field(default=None)
    additional_info: AdditionalInfo | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        new_data = data.copy()

        if "shift_state" in data:
            new_data["shift_state"] = ShiftState(data["shift_state"])

        if "indicators" in data:
            new_data["indicators"] = Indicators(**data["indicators"])

        if "additional_info" in data:
            new_data["additional_info"] = AdditionalInfo(**data["additional_info"])

        return cls(**new_data)
