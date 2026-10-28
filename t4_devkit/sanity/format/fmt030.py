from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT030"]


@CHECKERS.register()
class FMT030(TableFieldChecker):
    """A checker of FMT030."""

    id = RuleID("FMT030")
    name = RuleName("category-field")
    severity = Severity.ERROR
    description = "All 'Category' records are valid."
    table = SchemaName.CATEGORY
