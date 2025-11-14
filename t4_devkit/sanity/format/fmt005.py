from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT005"]


@CHECKERS.register()
class FMT005(FieldTypeChecker):
    """A checker of FMT005."""

    id = RuleID("FMT005")
    name = RuleName("instance-field")
    severity = Severity.ERROR
    description = "All types of 'Instance' fields are valid."
    schema = SchemaName.INSTANCE
