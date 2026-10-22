from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from t4_devkit.schema import SensorModality
from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC018"]


@CHECKERS.register()
class REC018(RecordsChecker):
    """A checker of REC018."""

    id = RuleID("REC018")
    name = RuleName("sample-frames")
    severity = Severity.ERROR
    description = (
        "A 'Sample' has at most one 'SampleData' per channel; its 'timestamp' is its LiDAR frame's "
        "(its earliest frame's if it has no LiDAR); 'has_key_frame' is true exactly when one of "
        "its 'SampleData' is a key frame."
    )
    tables = (SchemaName.SAMPLE, SchemaName.SAMPLE_DATA, SchemaName.SENSOR)

    def check(self, context: SanityContext) -> list[Reason] | None:
        sensors = {
            sensor.token: sensor for sensor in context.load_records(SchemaName.SENSOR).unwrap()
        }
        frames: dict[str, list] = defaultdict(list)
        for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap():
            if frame.sensor_token in sensors:  # unknown sensors: reported by the reference rules
                frames[frame.sample_token].append(frame)

        failures = []
        for sample in context.load_records(SchemaName.SAMPLE).unwrap():
            sample_frames = frames[sample.token]
            channels = [sensors[frame.sensor_token].channel for frame in sample_frames]
            for channel in sorted({c for c in channels if channels.count(c) > 1}):
                failures.append(Reason(f"Sample {sample.token}: several frames of {channel}"))
            if sample_frames:
                lidar_frames = [
                    frame
                    for frame in sample_frames
                    if sensors[frame.sensor_token].modality == SensorModality.LIDAR
                ]
                expected = min(frame.timestamp for frame in lidar_frames or sample_frames)
                if sample.timestamp != expected:
                    failures.append(
                        Reason(
                            f"Sample {sample.token}: 'timestamp' {sample.timestamp}, expected {expected}"
                        )
                    )
            has_key_frame = any(frame.is_key_frame for frame in sample_frames)
            if sample.has_key_frame != has_key_frame:
                failures.append(
                    Reason(f"Sample {sample.token}: 'has_key_frame' should be {has_key_frame}")
                )
        return failures or None
