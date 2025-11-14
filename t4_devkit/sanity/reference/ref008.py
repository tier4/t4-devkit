from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF008"]


@CHECKERS.register(RuleID("REF008"))
class REF008(RecordReferenceChecker):
    """A checker of REF008."""

    name = RuleName("calibrated-sensor-to-sensor")
    severity = Severity.ERROR
    description = "'CalibratedSensor.sensor_token' refers to 'Sensor' record."
    source = SchemaName.CALIBRATED_SENSOR
    target = SchemaName.SENSOR
    reference = "sensor_token"
