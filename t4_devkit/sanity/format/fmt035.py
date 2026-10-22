from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT035"]


@CHECKERS.register()
class FMT035(TableFieldChecker):
    """A checker of FMT035."""

    id = RuleID("FMT035")
    name = RuleName("object-ann-field")
    severity = Severity.ERROR
    description = "All 'ObjectAnn' records are valid."
    table = SchemaName.OBJECT_ANN
