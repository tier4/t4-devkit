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

__all__ = ["FMT005"]


@CHECKERS.register(RuleID("FMT005"))
class FMT005(Checker):
    """A checker of FMT005."""

    name = RuleName("instance-field")
    description = "All types of 'Instance' fields are valid."

    def check(self, context: SanityContext) -> list[Reason]:
        schema = SchemaName.INSTANCE
        match context.to_schema_file(schema):
            case Some(x):
                records = load_json_safe(x.as_posix())
                if not is_successful(records):
                    return [Reason("Invalid `Instance` file")]
                return build_records(schema, records.unwrap())
            case _:
                return [Reason("No `Instance` file found")]
