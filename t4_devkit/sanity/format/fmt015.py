from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT015"]


@CHECKERS.register()
class FMT015(FieldTypeChecker):
    """A checker of FMT015."""

    id = RuleID("FMT015")
    name = RuleName("object-ann-field")
    severity = Severity.ERROR
    description = "All types of 'ObjectAnn' fields are valid."
    schema = SchemaName.OBJECT_ANN
