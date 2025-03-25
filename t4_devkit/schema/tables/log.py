from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ["Log"]


@define(slots=False)
@SCHEMAS.register(SchemaName.LOG)
class Log(SchemaBase):
    """A dataclass to represent schema table of `log.json`.

    Attributes:
        token (str): Unique record identifier.
        logfile (str): Log file name.
        vehicle (str): Vehicle name.
        data_captured (str): Date of the data was captured (YYYY-MM-DD-HH-mm-ss).
        location (str): Area where log was captured.

    Shortcuts:
    ---------
        map_token (str): Foreign key pointing to the map record.
            This should be set after instantiated.
    """

    logfile: str = field(validator=validators.instance_of(str))
    vehicle: str = field(validator=validators.instance_of(str))
    data_captured: str = field(validator=validators.instance_of(str))
    location: str = field(validator=validators.instance_of(str))

    # shortcuts
    map_token: str = field(init=False, factory=str)
