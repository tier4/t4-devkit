from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT027"]


@CHECKERS.register()
class FMT027(TableFieldChecker):
    """A checker of FMT027."""

    id = RuleID("FMT027")
    name = RuleName("vehicle-field")
    severity = Severity.ERROR
    description = "All 'Vehicle' records are valid."
    table = SchemaName.VEHICLE
