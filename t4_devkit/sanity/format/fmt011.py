from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker


__all__ = ["FMT011"]


@CHECKERS.register(RuleID("FMT011"))
class FMT011(FieldTypeChecker):
    """A checker of FMT011."""

    name = RuleName("scene-field")
    description = "All types of 'Scene' fields are valid."
    schema = SchemaName.SCENE
