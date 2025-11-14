from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT003"]


@CHECKERS.register()
class FMT003(FieldTypeChecker):
    """A checker of FMT003."""

    id = RuleID("FMT003")
    name = RuleName("category-field")
    severity = Severity.ERROR
    description = "All types of 'Category' fields are valid."
    schema = SchemaName.CATEGORY
