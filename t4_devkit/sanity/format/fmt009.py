from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT009"]


@CHECKERS.register(RuleID("FMT009"))
class FMT009(FieldTypeChecker):
    """A checker of FMT009."""

    name = RuleName("sample-annotation-field")
    severity = Severity.ERROR
    description = "All types of 'SampleAnnotation' fields are valid."
    schema = SchemaName.SAMPLE_ANNOTATION
