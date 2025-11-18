from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT002"]


@CHECKERS.register()
class FMT002(FieldTypeChecker):
    """A checker of FMT002."""

    id = RuleID("FMT002")
    name = RuleName("calibrated-sensor-field")
    severity = Severity.ERROR
    description = "All types of 'CalibratedSensor' fields are valid."
    schema = SchemaName.CALIBRATED_SENSOR
