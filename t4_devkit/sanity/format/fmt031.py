from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT031"]


@CHECKERS.register()
class FMT031(TableFieldChecker):
    """A checker of FMT031."""

    id = RuleID("FMT031")
    name = RuleName("attribute-field")
    severity = Severity.ERROR
    description = "All 'Attribute' records are valid."
    table = SchemaName.ATTRIBUTE
