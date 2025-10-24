from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker

if TYPE_CHECKING:
    pass

__all__ = ["FMT004"]


@CHECKERS.register(RuleID("FMT004"))
class FMT004(FieldTypeChecker):
    """A checker of FMT004."""

    name = RuleName("ego-pose-field")
    description = "All types of 'EgoPose' fields are valid."
    schema = SchemaName.EGO_POSE
