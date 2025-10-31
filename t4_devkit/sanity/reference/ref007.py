from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import ReferenceChecker

__all__ = ["REF007"]


@CHECKERS.register(RuleID("REF007"))
class REF007(ReferenceChecker):
    """A checker of REF007."""

    name = RuleName("sample-data-to-calibrated-sensor")
    description = "'SampleData.calibrated_sensor_token' refers to 'CalibratedSensor' record."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.CALIBRATED_SENSOR
    reference = "calibrated_sensor_token"
