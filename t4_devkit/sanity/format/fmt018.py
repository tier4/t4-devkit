from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some
from returns.pipeline import is_successful

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe
from .utility import build_records

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["FMT018"]


@CHECKERS.register(RuleID("FMT018"))
class FMT018(Checker):
    """A checker of FMT018."""

    name = RuleName("vehicle-state-field")
    description = "All types of 'VehicleState' fields are valid."

    def check(self, context: SanityContext) -> list[Reason]:
        schema = SchemaName.VEHICLE_STATE
        match context.to_schema_file(schema):
            case Some(x):
                if not x.exists() and schema.is_optional():
                    return []
                records = load_json_safe(x.as_posix())
                if not is_successful(records):
                    return [Reason("Invalid `VehicleState` file")]
                return build_records(schema, records.unwrap())
            case _:
                return [Reason("No `VehicleState` file found")]
