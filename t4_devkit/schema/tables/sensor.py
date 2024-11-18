from __future__ import annotations

from enum import Enum

from attrs import define, field

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ("Sensor", "SensorModality")


class SensorModality(str, Enum):
    """An enum to represent sensor modalities.

    Attributes:
        LIDAR: Lidar sensor.
        CAMERA: Camera sensor.
        RADAR: Radar sensor.
    """

    LIDAR = "lidar"
    CAMERA = "camera"
    RADAR = "radar"


@define(slots=False)
@SCHEMAS.register(SchemaName.SENSOR)
class Sensor(SchemaBase):
    """A dataclass to represent schema table of `sensor.json`.

    Attributes:
        token (str): Unique record identifier.
        channel (str): Sensor channel name.
        modality (SensorModality): Sensor modality.

    Shortcuts:
        first_sd_token (str): The first sample data token corresponding to its sensor channel.
    """

    channel: str
    modality: SensorModality = field(converter=SensorModality)

    # shortcuts
    first_sd_token: str = field(init=False)

    @staticmethod
    def shortcuts() -> tuple[str] | None:
        return ("first_sd_token",)
