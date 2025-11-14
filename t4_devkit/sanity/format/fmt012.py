from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT012"]


@CHECKERS.register()
class FMT012(FieldTypeChecker):
    """A checker of FMT012."""

    id = RuleID("FMT012")
    name = RuleName("sensor-field")
    severity = Severity.ERROR
    description = "All types of 'Sensor' fields are valid."
    schema = SchemaName.SENSOR
