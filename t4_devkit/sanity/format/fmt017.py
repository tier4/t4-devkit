from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT017"]


@CHECKERS.register(RuleID("FMT017"))
class FMT017(FieldTypeChecker):
    """A checker of FMT017."""

    name = RuleName("keypoint-field")
    severity = Severity.ERROR
    description = "All types of 'Keypoint' fields are valid."
    schema = SchemaName.KEYPOINT
