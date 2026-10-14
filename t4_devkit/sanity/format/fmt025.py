from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT025"]


@CHECKERS.register()
class FMT025(TableFieldChecker):
    """A checker of FMT025."""

    id = RuleID("FMT025")
    name = RuleName("scene-field")
    severity = Severity.ERROR
    description = "All 'Scene' records are valid."
    table = SchemaName.SCENE
