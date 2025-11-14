from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT008"]


@CHECKERS.register()
class FMT008(FieldTypeChecker):
    """A checker of FMT008."""

    id = RuleID("FMT008")
    name = RuleName("sample-field")
    severity = Severity.ERROR
    description = "All types of 'Sample' fields are valid."
    schema = SchemaName.SAMPLE
