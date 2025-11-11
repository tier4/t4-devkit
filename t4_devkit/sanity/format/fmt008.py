from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker


__all__ = ["FMT008"]


@CHECKERS.register(RuleID("FMT008"))
class FMT008(FieldTypeChecker):
    """A checker of FMT008."""

    name = RuleName("sample-field")
    description = "All types of 'Sample' fields are valid."
    schema = SchemaName.SAMPLE
