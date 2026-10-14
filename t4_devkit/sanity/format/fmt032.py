from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT032"]


@CHECKERS.register()
class FMT032(TableFieldChecker):
    """A checker of FMT032."""

    id = RuleID("FMT032")
    name = RuleName("visibility-field")
    severity = Severity.ERROR
    description = "All 'Visibility' records are valid."
    table = SchemaName.VISIBILITY
