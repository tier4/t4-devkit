from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["REF008"]


@CHECKERS.register(RuleID("REF008"))
class REF008(Checker):
    """A checker of REF008."""

    name = RuleName("calibrated-sensor-to-sensor")
    description = "'CalibratedSensor.sensor_token' refers to 'Sensor' record."

    def check(self, context: SanityContext) -> list[Reason]:
        calibrated_sensor_file = context.to_schema_file(SchemaName.CALIBRATED_SENSOR)
        sensor_file = context.to_schema_file(SchemaName.SENSOR)
        match (calibrated_sensor_file, sensor_file):
            case Some(x), Some(y):
                calibrated_sensor = load_json_safe(x).unwrap()
                sensor_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(f"No reference to `CalibratedSensor.sensor_token`: {cs['sensor_token']}")
                    for cs in calibrated_sensor
                    if cs["sensor_token"] not in sensor_tokens
                ]
            case _:
                return [Reason("Missing `CalibratedSensor` or `Sensor` file")]
