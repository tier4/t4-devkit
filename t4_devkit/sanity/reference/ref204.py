from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..record.base import channel_file

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF204"]


@CHECKERS.register()
class REF204(RecordsChecker):
    """A checker of REF204."""

    id = RuleID("REF204")
    name = RuleName("sample-data-file-of-sensor")
    severity = Severity.ERROR
    description = (
        "For a channel stored in one file, 'SampleData.filename' is its sensor's "
        "'camera.video.path' / 'lidar.container.path'."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.SAMPLE_DATA,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        files = {
            sensor.token: stored[0]
            for sensor in context.load_records(SchemaName.SENSOR).unwrap()
            if (stored := channel_file(sensor)) is not None
        }
        return [
            Reason(
                f"SampleData {frame.token}: 'filename' {frame.filename}, sensor file {files[frame.sensor_token]}"
            )
            for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap()
            if frame.sensor_token in files and frame.filename != files[frame.sensor_token]
        ] or None
