from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT040"]


@CHECKERS.register()
class FMT040(TableFieldChecker):
    """A checker of FMT040."""

    id = RuleID("FMT040")
    name = RuleName("caption-field")
    severity = Severity.ERROR
    description = "All 'Caption' records are valid."
    table = SchemaName.CAPTION
