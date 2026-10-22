from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT033"]


@CHECKERS.register()
class FMT033(TableFieldChecker):
    """A checker of FMT033."""

    id = RuleID("FMT033")
    name = RuleName("instance-field")
    severity = Severity.ERROR
    description = "All 'Instance' records are valid."
    table = SchemaName.INSTANCE
