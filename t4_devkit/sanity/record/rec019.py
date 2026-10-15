from __future__ import annotations

from typing import TYPE_CHECKING

from collections import defaultdict

from t4_devkit.schema.v1 import SchemaName

from .base import channel_file

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC019"]


@CHECKERS.register()
class REC019(RecordsChecker):
    """A checker of REC019."""

    id = RuleID("REC019")
    name = RuleName("channel-frames")
    severity = Severity.ERROR
    description = (
        "For a channel stored in one file, 'frame_count' equals the number of its 'SampleData' "
        "records, and their 'frame_index' values are 0 to 'frame_count - 1', each once."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.SAMPLE_DATA,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        sensors = context.load_records(SchemaName.SENSOR).unwrap()
        # source LiDARs of a merged channel have no frames of their own
        sources = {
            channel
            for sensor in sensors
            if sensor.lidar is not None
            for channel in sensor.lidar.source_channels
        }
        indices: dict[str, list[int | None]] = defaultdict(list)
        for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap():
            indices[frame.sensor_token].append(frame.frame_index)
        failures = []
        for sensor in sensors:
            stored = channel_file(sensor)
            if stored is None or sensor.channel in sources:
                continue
            _, frame_count = stored
            if sorted(indices[sensor.token], key=lambda i: -1 if i is None else i) != list(
                range(frame_count)
            ):
                failures.append(
                    Reason(
                        f"Sensor {sensor.channel} ({sensor.token}): 'frame_count' {frame_count}, "
                        f"{len(indices[sensor.token])} frames, 'frame_index' not 0 to {frame_count - 1}"
                    )
                )
        return failures or None
