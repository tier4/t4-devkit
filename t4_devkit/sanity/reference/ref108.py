from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF108"]


@CHECKERS.register()
class REF108(RecordsChecker):
    """A checker of REF108."""

    id = RuleID("REF108")
    name = RuleName("links-same-stream")
    severity = Severity.ERROR
    description = (
        "'SampleData.next' is of the same channel, and 'SampleAnnotation.next' of the same "
        "instance."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.SAMPLE_DATA,
        SchemaName.SAMPLE_ANNOTATION,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        channels = {
            sensor.token: sensor.channel
            for sensor in context.load_records(SchemaName.SENSOR).unwrap()
        }
        frames = {
            frame.token: frame for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap()
        }
        anns = {
            ann.token: ann for ann in context.load_records(SchemaName.SAMPLE_ANNOTATION).unwrap()
        }
        failures = [
            Reason(f"SampleData {frame.token}: 'next' is of another channel")
            for frame in frames.values()
            if frame.next in frames
            and channels.get(frames[frame.next].sensor_token) != channels.get(frame.sensor_token)
        ]
        failures += [
            Reason(f"SampleAnnotation {ann.token}: 'next' is of another instance")
            for ann in anns.values()
            if ann.next in anns and anns[ann.next].instance_token != ann.instance_token
        ]
        return failures or None
