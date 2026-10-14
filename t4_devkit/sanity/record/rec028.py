from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity, record_name
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC028"]


@CHECKERS.register()
class REC028(RecordsChecker):
    """A checker of REC028."""

    id = RuleID("REC028")
    name = RuleName("labels-on-key-frames")
    severity = Severity.ERROR
    description = (
        "Labels sit on key frames: a 'SampleAnnotation' on a 'Sample' with 'has_key_frame', an "
        "'ObjectAnn' or 'Keypoint' on a 'SampleData' with 'is_key_frame'."
    )
    tables = (
        SchemaName.SAMPLE,
        SchemaName.SAMPLE_DATA,
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.OBJECT_ANN,
        SchemaName.KEYPOINT,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        key_samples = {
            sample.token
            for sample in context.load_records(SchemaName.SAMPLE).unwrap()
            if sample.has_key_frame
        }
        key_frames = {
            frame.token
            for frame in context.load_records(SchemaName.SAMPLE_DATA).unwrap()
            if frame.is_key_frame
        }
        failures = [
            Reason(f"SampleAnnotation {ann.token}: sample without a key frame")
            for ann in context.load_records(SchemaName.SAMPLE_ANNOTATION).unwrap()
            if ann.sample_token not in key_samples
        ]
        for table in (SchemaName.OBJECT_ANN, SchemaName.KEYPOINT):
            failures += [
                Reason(f"{record_name(table)} {ann.token}: not on a key frame")
                for ann in context.load_records(table).unwrap()
                if ann.sample_data_token not in key_frames
            ]
        return failures or None
