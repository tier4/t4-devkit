from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from .base import channel_file, frame_formats

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC020"]


@CHECKERS.register()
class REC020(RecordsChecker):
    """A checker of REC020."""

    id = RuleID("REC020")
    name = RuleName("sensor-storage-consistent")
    severity = Severity.ERROR
    description = (
        "'SampleData.frame_index' is 'null' exactly when its sensor stores one file per frame, "
        "and 'fileformat' matches the sensor's storage."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.SAMPLE_DATA,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        sensors = {
            sensor.token: sensor for sensor in context.load_records(SchemaName.SENSOR).unwrap()
        }
        failures = []
        for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap():
            sensor = sensors.get(frame.sensor_token)
            if sensor is None:
                continue  # reported by the reference rules
            one_file = channel_file(sensor) is not None
            if one_file != (frame.frame_index is not None):
                expected = "a 'frame_index'" if one_file else "no 'frame_index'"
                failures.append(Reason(f"SampleData {frame.token}: needs {expected}"))
            formats = frame_formats(sensor)
            if frame.fileformat.value not in formats:
                failures.append(
                    Reason(
                        f"SampleData {frame.token}: 'fileformat' {frame.fileformat.value}, "
                        f"sensor {sensor.channel} stores {' / '.join(sorted(formats))}"
                    )
                )
        return failures or None
