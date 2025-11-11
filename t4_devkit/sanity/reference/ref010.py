from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF010"]


@CHECKERS.register(RuleID("REF010"))
class REF010(RecordReferenceChecker):
    """A checker of REF010."""

    name = RuleName("instance-to-first-sample-annotation")
    severity = Severity.ERROR
    description = "'Instance.first_annotation_token' refers to 'SampleAnnotation' record."
    source = SchemaName.INSTANCE
    target = SchemaName.SAMPLE_ANNOTATION
    reference = "first_annotation_token"
