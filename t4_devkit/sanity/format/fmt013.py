from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT013"]


@CHECKERS.register()
class FMT013(FieldTypeChecker):
    """A checker of FMT013."""

    id = RuleID("FMT013")
    name = RuleName("visibility-field")
    severity = Severity.ERROR
    description = "All types of 'Visibility' fields are valid."
    schema = SchemaName.VISIBILITY
