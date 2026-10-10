from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase

from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["Vehicle"]


@define(slots=False)
@SCHEMAS.register(SchemaName.VEHICLE)
class Vehicle(SchemaBase):
    """`vehicle.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        model (str): Vehicle model.
        length (float): Length [m].
        width (float): Width [m].
        height (float): Height [m].
        wheel_base (float): Wheel base [m].
        rear_axle_to_center (float | None): Distance from the rear axle to the vehicle center [m].
        sensor_rig_id (str | None): Sensor rig ID.
        name (str | None): Vehicle name, e.g. "j6_gen2_04".
    """

    model: str = field(validator=validators.instance_of(str))
    length: float = field(validator=(validators.instance_of((int, float)), validators.gt(0)))
    width: float = field(validator=(validators.instance_of((int, float)), validators.gt(0)))
    height: float = field(validator=(validators.instance_of((int, float)), validators.gt(0)))
    wheel_base: float = field(validator=(validators.instance_of((int, float)), validators.gt(0)))
    rear_axle_to_center: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    sensor_rig_id: str | None = field(validator=validators.optional(validators.instance_of(str)))
    name: str | None = field(validator=validators.optional(validators.instance_of(str)))
