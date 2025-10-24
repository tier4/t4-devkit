from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker

if TYPE_CHECKING:
    pass

__all__ = ["FMT012"]


@CHECKERS.register(RuleID("FMT012"))
class FMT012(FieldTypeChecker):
    """A checker of FMT012."""

    name = RuleName("sensor-field")
    description = "All types of 'Sensor' fields are valid."
    schema = SchemaName.SENSOR
