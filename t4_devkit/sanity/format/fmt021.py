from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT021"]


@CHECKERS.register()
class FMT021(TableFieldChecker):
    """A checker of FMT021."""

    id = RuleID("FMT021")
    name = RuleName("sample-field")
    severity = Severity.ERROR
    description = "All 'Sample' records are valid."
    table = SchemaName.SAMPLE
