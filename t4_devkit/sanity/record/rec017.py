from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import AnnotationType, SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC017"]


@CHECKERS.register()
class REC017(RecordsChecker):
    """A checker of REC017."""

    id = RuleID("REC017")
    name = RuleName("automatic-label-provenance")
    severity = Severity.WARNING
    description = (
        "Labels that are not 'manual' have a 'provenance', and 'auto' / 'pseudo' labels a "
        "'confidence'."
    )
    tables = (
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.OBJECT_ANN,
        SchemaName.KEYPOINT,
        SchemaName.TRAFFIC_LIGHT,
        SchemaName.SCENARIO,
        SchemaName.CAPTION,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        failures = []
        for table in self.tables:
            for label in context.load_records(table).unwrap():
                if label.annotation_type == AnnotationType.MANUAL:
                    continue
                if label.provenance is None:
                    failures.append(Reason(f"{table.value} {label.token}: no 'provenance'"))
                scored = label.annotation_type in (AnnotationType.AUTO, AnnotationType.PSEUDO)
                # `traffic_light` has no record-level confidence
                if scored and hasattr(label, "confidence") and label.confidence is None:
                    failures.append(Reason(f"{table.value} {label.token}: no 'confidence'"))
        return failures or None
