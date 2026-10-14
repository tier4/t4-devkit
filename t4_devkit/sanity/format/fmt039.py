from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT039"]


@CHECKERS.register()
class FMT039(TableFieldChecker):
    """A checker of FMT039."""

    id = RuleID("FMT039")
    name = RuleName("scenario-field")
    severity = Severity.ERROR
    description = "All 'Scenario' records are valid."
    table = SchemaName.SCENARIO
