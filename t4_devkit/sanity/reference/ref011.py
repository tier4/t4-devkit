from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import RecordReferenceChecker


__all__ = ["REF011"]


@CHECKERS.register(RuleID("REF011"))
class REF011(RecordReferenceChecker):
    """A checker of REF011."""

    name = RuleName("instance-to-last-sample-annotation")
    description = "'Instance.last_annotation_token' refers to 'SampleAnnotation' record."
    source = SchemaName.INSTANCE
    target = SchemaName.SAMPLE_ANNOTATION
    reference = "last_annotation_token"
