from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful

from t4_devkit.schema import SCHEMAS, SchemaName
from t4_devkit.schema.v1 import SCHEMAS as V1_SCHEMAS
from t4_devkit.schema.v1 import SchemaName as V1SchemaName

from ..checker import Checker, ManifestChecker
from ..result import Reason
from ..safety import load_json_safe, load_schema_safe

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
        conversion = load_schema_safe(module, record)
        if not is_successful(conversion):
            failures.append(Reason(f"[{schema.name}] {record['token']}: {conversion.failure()}"))
    return failures if failures else None


class TableFieldChecker(ManifestChecker):
    """Base class for 1.0 format checkers: every record of a table builds into its 1.0 class.

    Attributes:
        table (V1SchemaName): The 1.0 table to check.
    """

    table: V1SchemaName

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match super().can_skip(context):
            case Some(reason):
                return Some(reason)
        if (
            not self.table.is_optional()
            and self.table.value not in context.manifest.unwrap().tables
        ):
            return Maybe.from_value(Reason(f"'{self.table.value}' not listed (see STR014)"))
        return Nothing

    def check(self, context: SanityContext) -> list[Reason] | None:
        if self.table.value not in context.manifest.unwrap().tables:
            return None  # optional table not present
        match context.load_table(self.table):
            case Some(records):
                return _build_v1_records(self.table, records)
        return [Reason(f"'{context.to_table_file(self.table).unwrap()}' cannot be read")]


def _build_v1_records(table: V1SchemaName, records: list[dict]) -> list[Reason] | None:
    module = V1_SCHEMAS.get(table)
    failures = []
    for record in records:
        conversion = load_schema_safe(module, record)
        if not is_successful(conversion):
            token = record.get("token") if isinstance(record, dict) else None
            failures.append(Reason(f"[{table.name}] {token}: {conversion.failure()}"))
    return failures if failures else None
