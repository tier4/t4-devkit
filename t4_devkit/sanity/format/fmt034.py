from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT034"]


@CHECKERS.register()
class FMT034(TableFieldChecker):
    """A checker of FMT034."""

    id = RuleID("FMT034")
    name = RuleName("sample-annotation-field")
    severity = Severity.ERROR
    description = "All 'SampleAnnotation' records are valid."
    table = SchemaName.SAMPLE_ANNOTATION
