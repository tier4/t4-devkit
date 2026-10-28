from __future__ import annotations

from enum import Enum, unique

from attrs import converters, define, field, validators

from t4_devkit.schema.tables.base import SchemaBase
from t4_devkit.schema.tables.vehicle_state import Indicators

from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["ShiftState", "VehicleStateSource", "VehicleState"]


@unique
class ShiftState(str, Enum):
    """Gear shift state, as in Autoware GearReport."""

    PARK = "PARK"
    REVERSE = "REVERSE"
    NEUTRAL = "NEUTRAL"
    DRIVE = "DRIVE"
    LOW = "LOW"
    NONE = "NONE"
    UNKNOWN = "unknown"


@unique
class VehicleStateSource(str, Enum):
    """Where vehicle signals came from."""

    CAN = "can"
    VEHICLE_INTERFACE = "vehicle_interface"
    IMU = "imu"


@define(slots=False)
@SCHEMAS.register(SchemaName.VEHICLE_STATE)
class VehicleState(SchemaBase):
    """`vehicle_state.json` dataclass.

    Measured vehicle signals at their native rate (not resampled).

    Attributes:
        token (str): Unique record identifier.
        timestamp (int): Unix time stamp [us].
        accel_pedal (float | None): Accelerator pedal position.
        brake_pedal (float | None): Brake pedal position.
        steer_pedal (float | None): Steering position.
        steering_tire_angle (float | None): Steering tire angle [rad].
        steering_wheel_angle (float | None): Steering wheel angle [rad].
        shift_state (ShiftState | None): Gear shift state.
        indicators (Indicators | None): Turn indicator and hazard state.
        longitudinal_velocity (float | None): Longitudinal velocity [m/s].
        lateral_velocity (float | None): Lateral velocity [m/s].
        heading_rate (float | None): Heading rate [rad/s].
        source (VehicleStateSource): Where the signals came from.
    """

    timestamp: int = field(validator=validators.instance_of(int))
    accel_pedal: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    brake_pedal: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    steer_pedal: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    steering_tire_angle: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    steering_wheel_angle: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    shift_state: ShiftState | None = field(converter=converters.optional(ShiftState))
    indicators: Indicators | None = field(
        converter=lambda x: Indicators(**x) if isinstance(x, dict) else x,
        validator=validators.optional(validators.instance_of(Indicators)),
    )
    longitudinal_velocity: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    lateral_velocity: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    heading_rate: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    source: VehicleStateSource = field(converter=VehicleStateSource)
