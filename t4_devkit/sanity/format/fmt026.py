from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT026"]


@CHECKERS.register()
class FMT026(TableFieldChecker):
    """A checker of FMT026."""

    id = RuleID("FMT026")
    name = RuleName("log-field")
    severity = Severity.ERROR
    description = "All 'Log' records are valid."
    table = SchemaName.LOG
