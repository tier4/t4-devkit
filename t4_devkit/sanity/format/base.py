from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import Result, safe

from t4_devkit.schema import SCHEMAS, SchemaBase, SchemaName

from ..checker import Checker
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext


class FieldTypeChecker(Checker):
    """Base class for format checkers.

    Attributes:
        id (RuleID): The ID of the rule.
        name (RuleName): The name of the rule.
        severity (Severity): The severity of the rule.
        description (str): The description of the rule.
        schema (SchemaName): The schema name to check.
    """

    schema: SchemaName

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match context.to_schema_file(self.schema):
            case Some(x):
                if not x.exists() and not self.schema.is_optional():
                    return Maybe.from_value(Reason(f"No '{self.schema.filename}' found"))
                return Nothing
            case _:
                return Nothing

    def check(self, context: SanityContext) -> list[Reason] | None:
        filepath = context.to_schema_file(self.schema).unwrap()

        if self.schema.is_optional() and not filepath.exists():
            return None

        records = load_json_safe(filepath)
        return _build_records(self.schema, records.unwrap())


def _build_records(schema: SchemaName, records: list[dict]) -> list[Reason] | None:
    module = SCHEMAS.get(schema)
    failures = []
    for record in records:
        conversion = _safe_from_dict(module, record)
        if not is_successful(conversion):
            failures.append(Reason(f"[{schema.name}] {record['token']}: {conversion.failure()}"))
    return failures if failures else None


@safe
def _safe_from_dict(module: type[SchemaBase], record: dict) -> Result[SchemaBase, Exception]:
    return module.from_dict(record)
