from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT004"]


@CHECKERS.register()
class FMT004(FieldTypeChecker):
    """A checker of FMT004."""

    id = RuleID("FMT004")
    name = RuleName("ego-pose-field")
    severity = Severity.ERROR
    description = "All types of 'EgoPose' fields are valid."
    schema = SchemaName.EGO_POSE
