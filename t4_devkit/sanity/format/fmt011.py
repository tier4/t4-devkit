from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker

if TYPE_CHECKING:
    pass

__all__ = ["FMT011"]


@CHECKERS.register(RuleID("FMT011"))
class FMT011(FieldTypeChecker):
    """A checker of FMT011."""

    name = RuleName("scene-field")
    description = "All types of 'Scene' fields are valid."
    schema = SchemaName.SCENE
