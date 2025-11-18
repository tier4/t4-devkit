from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT011"]


@CHECKERS.register()
class FMT011(FieldTypeChecker):
    """A checker of FMT011."""

    id = RuleID("FMT011")
    name = RuleName("scene-field")
    severity = Severity.ERROR
    description = "All types of 'Scene' fields are valid."
    schema = SchemaName.SCENE
