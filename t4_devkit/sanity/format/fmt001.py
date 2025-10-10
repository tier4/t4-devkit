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

__all__ = ["FMT001"]


@CHECKERS.register(RuleID("FMT001"))
class FMT001(Checker):
    """A checker of FMT001."""

    name = RuleName("attribute-field")
    description = "All types of 'Attribute' fields are valid."

    def check(self, context: SanityContext) -> list[Reason]:
        schema = SchemaName.ATTRIBUTE
        match context.to_schema_file(schema):
            case Some(x):
                records = load_json_safe(x.as_posix())
                if not is_successful(records):
                    return [Reason("Invalid `Attribute` file")]
                return build_records(schema, records.unwrap())
            case _:
                return [Reason("No `Attribute` file found")]
