from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT029"]


@CHECKERS.register()
class FMT029(TableFieldChecker):
    """A checker of FMT029."""

    id = RuleID("FMT029")
    name = RuleName("vehicle-state-field")
    severity = Severity.ERROR
    description = "All 'VehicleState' records are valid."
    table = SchemaName.VEHICLE_STATE
