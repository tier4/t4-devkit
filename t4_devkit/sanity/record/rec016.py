from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import AnnotationType, SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity, record_name
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC016"]


@CHECKERS.register()
class REC016(RecordsChecker):
    """A checker of REC016."""

    id = RuleID("REC016")
    name = RuleName("manual-label-confidence")
    severity = Severity.ERROR
    description = "Labels with 'annotation_type: manual' have 'confidence: null'."
    tables = (
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.OBJECT_ANN,
        SchemaName.KEYPOINT,
        SchemaName.TRAFFIC_LIGHT,
        SchemaName.SCENARIO,
        SchemaName.CAPTION,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return [
            Reason(
                f"{record_name(table)} {label.token}: manual label with 'confidence' {label.confidence}"
            )
            for table in self.tables
            for label in context.load_records(table).unwrap()
            if label.annotation_type == AnnotationType.MANUAL
            and getattr(label, "confidence", None) is not None
        ] or None
