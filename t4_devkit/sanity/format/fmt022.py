from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT022"]


@CHECKERS.register()
class FMT022(TableFieldChecker):
    """A checker of FMT022."""

    id = RuleID("FMT022")
    name = RuleName("sample-data-field")
    severity = Severity.ERROR
    description = "All 'SampleData' records are valid."
    table = SchemaName.SAMPLE_DATA
