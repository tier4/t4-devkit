from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT001"]


@CHECKERS.register(RuleID("FMT001"))
class FMT001(FieldTypeChecker):
    """A checker of FMT001."""

    name = RuleName("attribute-field")
    severity = Severity.ERROR
    description = "All types of 'Attribute' fields are valid."
    schema = SchemaName.ATTRIBUTE
