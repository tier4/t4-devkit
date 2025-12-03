from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF104"]


@CHECKERS.register()
class REF104(RecordReferenceChecker):
    """A checker of REF104."""

    id = RuleID("REF104")
    name = RuleName("sample-annotation-prev-to-another")
    severity = Severity.ERROR
    description = "'SampleAnnotation.prev' refers to another one unless it is empty."
    source = SchemaName.SAMPLE_ANNOTATION
    target = SchemaName.SAMPLE_ANNOTATION
    reference = "prev"
