from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT007"]


@CHECKERS.register(RuleID("FMT007"))
class FMT007(FieldTypeChecker):
    """A checker of FMT007."""

    name = RuleName("map-field")
    severity = Severity.ERROR
    description = "All types of 'Map' fields are valid."
    schema = SchemaName.MAP
