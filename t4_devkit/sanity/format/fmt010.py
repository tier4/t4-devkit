from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT010"]


@CHECKERS.register()
class FMT010(FieldTypeChecker):
    """A checker of FMT010."""

    id = RuleID("FMT010")
    name = RuleName("sample-data-field")
    severity = Severity.ERROR
    description = "All types of 'SampleData' fields are valid."
    schema = SchemaName.SAMPLE_DATA
