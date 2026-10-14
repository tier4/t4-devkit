from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT023"]


@CHECKERS.register()
class FMT023(TableFieldChecker):
    """A checker of FMT023."""

    id = RuleID("FMT023")
    name = RuleName("ego-pose-field")
    severity = Severity.ERROR
    description = "All 'EgoPose' records are valid."
    table = SchemaName.EGO_POSE
