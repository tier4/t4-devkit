from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker

if TYPE_CHECKING:
    pass

__all__ = ["FMT018"]


@CHECKERS.register(RuleID("FMT018"))
class FMT018(FieldTypeChecker):
    """A checker of FMT018."""

    name = RuleName("vehicle-state-field")
    description = "All types of 'VehicleState' fields are valid."
    schema = SchemaName.VEHICLE_STATE
