from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF103"]


@CHECKERS.register()
class REF103(RecordReferenceChecker):
    """A checker of REF103."""

    id = RuleID("REF103")
    name = RuleName("sample-annotation-next-to-another")
    severity = Severity.ERROR
    description = "'SampleAnnotation.next' refers to another one unless it is empty."
    source = SchemaName.SAMPLE_ANNOTATION
    target = SchemaName.SAMPLE_ANNOTATION
    reference = "next"
