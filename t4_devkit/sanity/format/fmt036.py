from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT036"]


@CHECKERS.register()
class FMT036(TableFieldChecker):
    """A checker of FMT036."""

    id = RuleID("FMT036")
    name = RuleName("keypoint-field")
    severity = Severity.ERROR
    description = "All 'Keypoint' records are valid."
    table = SchemaName.KEYPOINT
