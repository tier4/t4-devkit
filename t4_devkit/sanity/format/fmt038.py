from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT038"]


@CHECKERS.register()
class FMT038(TableFieldChecker):
    """A checker of FMT038."""

    id = RuleID("FMT038")
    name = RuleName("route-field")
    severity = Severity.ERROR
    description = "All 'Route' records are valid."
    table = SchemaName.ROUTE
