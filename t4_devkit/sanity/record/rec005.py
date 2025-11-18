from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import RecordCountChecker

__all__ = ["REC005"]


@CHECKERS.register()
class REC005(RecordCountChecker):
    """A checker of REC005."""

    id = RuleID("REC005")
    name = RuleName("calibrated-sensor-not-empty")
    severity = Severity.ERROR
    description = "'CalibratedSensor' record is not empty."
    schema = SchemaName.CALIBRATED_SENSOR

    def check_count(self, records: list[dict]) -> list[Reason] | None:
        num_calibrated_sensor = len(records)
        return (
            [Reason("'CalibratedSensor' record must not be empty")]
            if num_calibrated_sensor == 0
            else None
        )
