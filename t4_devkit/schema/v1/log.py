from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["Log"]


@define(slots=False)
@SCHEMAS.register(SchemaName.LOG)
class Log(SchemaBase):
    """`log.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        logfile (str | None): Log file name.
        vehicle_token (str): Foreign key pointing to the vehicle.
        data_captured (str): Capture time, ISO 8601.
        location (str | None): Location of the recording.
        map_token (str | None): Foreign key pointing to the map, or None if there is no map.
    """

    logfile: str | None = field(validator=validators.optional(validators.instance_of(str)))
    vehicle_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    data_captured: str = field(validator=validators.instance_of(str))
    location: str | None = field(validator=validators.optional(validators.instance_of(str)))
    map_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
