from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker

if TYPE_CHECKING:
    pass

__all__ = ["FMT006"]


@CHECKERS.register(RuleID("FMT006"))
class FMT006(FieldTypeChecker):
    """A checker of FMT006."""

    name = RuleName("log-field")
    description = "All types of 'Log' fields are valid."
    schema = SchemaName.LOG
