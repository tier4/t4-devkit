from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some

from t4_devkit.schema import SchemaName

from ..checker import Checker
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext


class RecordCountChecker(Checker):
    """Base class for record count checkers."""

    schema: SchemaName

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match context.to_schema_file(self.schema):
            case Some(x):
                if not x.exists():
                    return Maybe.from_value(Reason(f"Missing {self.schema.filename}"))
                else:
                    return Nothing
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))

    def check(self, context: SanityContext) -> list[Reason]:
        filepath = context.to_schema_file(self.schema).unwrap()
        records = load_json_safe(filepath).unwrap()
        return self.check_count(records)

    @abstractmethod
    def check_count(self, records: list[dict]) -> list[Reason]:
        pass
