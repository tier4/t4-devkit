from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["REC007"]


@CHECKERS.register()
class REC007(Checker):
    """A checker of REC007."""

    id = RuleID("REC007")
    name = RuleName("category-indices-consistent")
    severity = Severity.ERROR
    description = "All categories must either have a unique 'index' or all have a 'null' index."
    schema = SchemaName.CATEGORY

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match context.to_schema_file(self.schema):
            case Some(x):
                if not x.exists():
                    return Maybe.from_value(Reason(f"Missing {self.schema.filename}"))
                else:
                    return Nothing
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()

        indices = [record.get("index") for record in records]
        all_none = all(index is None for index in indices)
        if all_none:
            return None

        some_none = any(index is None for index in indices)
        if some_none:
            return [
                Reason("All categories either must have an 'index' set or all have a 'null' index.")
            ]

        has_duplicates = len(set(indices)) < len(indices)
        if has_duplicates:
            return [Reason("Categories must have unique 'index' values.")]

        return None
