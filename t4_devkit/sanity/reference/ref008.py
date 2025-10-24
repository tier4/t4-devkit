from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import ReferenceChecker

if TYPE_CHECKING:
    pass

__all__ = ["REF008"]


@CHECKERS.register(RuleID("REF008"))
class REF008(ReferenceChecker):
    """A checker of REF008."""

    name = RuleName("calibrated-sensor-to-sensor")
    description = "'CalibratedSensor.sensor_token' refers to 'Sensor' record."
    source = SchemaName.CALIBRATED_SENSOR
    target = SchemaName.SENSOR
    reference = "sensor_token"
