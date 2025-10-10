from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some
from returns.pipeline import is_successful

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["SCH005"]


@CHECKERS.register(RuleID("SCH005"))
class SCH005(Checker):
    """A checker of SCH005."""

    name = RuleName("calibrated-sensor-not-empty")
    description = "'CalibratedSensor' record is not empty."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.to_schema_file(SchemaName.CALIBRATED_SENSOR):
            case Some(x):
                result = load_json_safe(x.as_posix())
                if not is_successful(result):
                    return [Reason("Failed to load 'CalibratedSensor' file")]
                else:
                    num_calibrated_sensor = len(result.unwrap())
                    return (
                        [] if num_calibrated_sensor > 0 else [Reason("No 'CalibratedSensor' found")]
                    )
            case _:
                return [Reason("Failed to load 'CalibratedSensor' file")]
