from __future__ import annotations

from typing import TYPE_CHECKING

from collections import defaultdict

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC021"]


@CHECKERS.register()
class REC021(RecordsChecker):
    """A checker of REC021."""

    id = RuleID("REC021")
    name = RuleName("timestamps-ordered")
    severity = Severity.ERROR
    description = (
        "Timestamps increase along 'next' ('Sample', 'SampleData', 'SampleAnnotation'), and "
        "'frame_index' follows timestamp order within a channel file."
    )
    tables = (
        SchemaName.SAMPLE,
        SchemaName.SAMPLE_DATA,
        SchemaName.SAMPLE_ANNOTATION,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        samples = {
            sample.token: sample for sample in context.load_records(SchemaName.SAMPLE).unwrap()
        }
        frames = {
            frame.token: frame for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap()
        }
        anns = {
            ann.token: ann for ann in context.load_records(SchemaName.SAMPLE_ANNOTATION).unwrap()
        }

        def ann_time(token: str) -> int | None:
            sample = samples.get(anns[token].sample_token)
            return None if sample is None else sample.timestamp

        failures = []
        for name, records, time in (
            ("Sample", samples, lambda token: samples[token].timestamp),
            ("SampleData", frames, lambda token: frames[token].timestamp),
            ("SampleAnnotation", anns, ann_time),
        ):
            for token, record in records.items():
                if record.next in records:
                    current, following = time(token), time(record.next)
                    if current is not None and following is not None and following <= current:
                        failures.append(Reason(f"{name} {token}: 'next' is not later"))

        by_sensor: dict[str, list] = defaultdict(list)
        for frame in frames.values():
            if frame.frame_index is not None:
                by_sensor[frame.sensor_token].append(frame)
        for sensor_token, sensor_frames in by_sensor.items():
            ordered = sorted(sensor_frames, key=lambda frame: frame.frame_index)
            if any(a.timestamp >= b.timestamp for a, b in zip(ordered, ordered[1:])):
                failures.append(
                    Reason(f"Sensor {sensor_token}: 'frame_index' not in timestamp order")
                )
        return failures or None
