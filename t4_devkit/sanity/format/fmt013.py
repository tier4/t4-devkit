from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker

if TYPE_CHECKING:
    pass

__all__ = ["FMT013"]


@CHECKERS.register(RuleID("FMT013"))
class FMT013(FieldTypeChecker):
    """A checker of FMT013."""

    name = RuleName("visibility-field")
    description = "All types of 'Visibility' fields are valid."
    schema = SchemaName.VISIBILITY
