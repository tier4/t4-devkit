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

__all__ = ["REF007"]


@CHECKERS.register(RuleID("REF007"))
class REF007(Checker):
    """A checker of REF007."""

    name = RuleName("sample-data-to-calibrated-sensor")
    description = "'SampleData.calibrated_sensor_token' refers to 'CalibratedSensor' record."

    def check(self, context: SanityContext) -> list[Reason]:
        sample_data_file = context.to_schema_file(SchemaName.SAMPLE_DATA)
        calibrated_sensor_file = context.to_schema_file(SchemaName.CALIBRATED_SENSOR)
        match (sample_data_file, calibrated_sensor_file):
            case Some(x), Some(y):
                sample_data = load_json_safe(x).unwrap()
                calibrated_sensor_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(
                        f"No reference to `SampleData.calibrated_sensor_token`: {s['calibrated_sensor_token']}"
                    )
                    for s in sample_data
                    if s["calibrated_sensor_token"] not in calibrated_sensor_tokens
                ]
            case _:
                return [Reason("Missing `SampleData` or `CalibratedSensor` file")]
