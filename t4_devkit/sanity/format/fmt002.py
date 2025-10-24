from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import FieldTypeChecker

if TYPE_CHECKING:
    pass

__all__ = ["FMT002"]


@CHECKERS.register(RuleID("FMT002"))
class FMT002(FieldTypeChecker):
    """A checker of FMT002."""

    name = RuleName("calibrated-sensor-field")
    description = "All types of 'CalibratedSensor' fields are valid."
    schema = SchemaName.CALIBRATED_SENSOR
