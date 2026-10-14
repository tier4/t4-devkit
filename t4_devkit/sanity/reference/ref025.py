from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SensorModality
from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF025"]


@CHECKERS.register()
class REF025(RecordsChecker):
    """A checker of REF025."""

    id = RuleID("REF025")
    name = RuleName("lidar-source-channels")
    severity = Severity.ERROR
    description = "'Lidar.source_channels' name LiDAR 'Sensor' records that have no 'SampleData'."
    tables = (
        SchemaName.SENSOR,
        SchemaName.SAMPLE_DATA,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        sensors = context.load_records(SchemaName.SENSOR).unwrap()
        with_frames = {
            frame.sensor_token for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap()
        }
        sources = {
            sensor.channel
            for sensor in sensors
            if sensor.modality == SensorModality.LIDAR and sensor.token not in with_frames
        }
        return [
            Reason(
                f"Sensor {sensor.channel}: source channel {channel} is not a LiDAR without frames"
            )
            for sensor in sensors
            if sensor.lidar is not None
            for channel in sensor.lidar.source_channels
            if channel not in sources
        ] or None
