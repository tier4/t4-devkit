from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT028"]


@CHECKERS.register()
class FMT028(TableFieldChecker):
    """A checker of FMT028."""

    id = RuleID("FMT028")
    name = RuleName("map-field")
    severity = Severity.ERROR
    description = "All 'Map' records are valid."
    table = SchemaName.MAP
