from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful

from ..checker import Checker, record_name
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from t4_devkit.schema import SchemaName
    from t4_devkit.schema.v1 import SchemaName as V1SchemaName

    from ..context import SanityContext


class RecordReferenceChecker(Checker):
    """Base class for record reference checkers.

    Attributes:
        id (RuleID): The ID of the rule.
        name (RuleName): The name of the rule.
        severity (Severity): The severity of the rule.
        description (str): The description of the rule.
        source (SchemaName): The source schema name.
        target (SchemaName | list[SchemaName]): The target schema name(s).
        reference (str): The reference token name in the source record.
    """

    source: SchemaName
    target: SchemaName | list[SchemaName]
    reference: str

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        target_schemas = self.target if isinstance(self.target, list) else [self.target]
        source_file = context.to_schema_file(self.source)
        target_files = [context.to_schema_file(t) for t in target_schemas]
        match (source_file, *target_files):
            case Some(x), *ys:
                target_file_paths = [y.unwrap() for y in ys if is_successful(y)]
                if not x.exists():
                    return Maybe.from_value(Reason(f"Missing {self.source.filename}"))
                elif not is_successful(load_json_safe(x)):
                    return Maybe.from_value(Reason(f"Cannot read {self.source.filename}"))
                elif not any(path.exists() for path in target_file_paths):
                    return Maybe.from_value(
                        Reason(f"Missing {', '.join(t.filename for t in target_schemas)}")
                    )
                else:
                    return Nothing
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        target_schemas = self.target if isinstance(self.target, list) else [self.target]
        source_file = context.to_schema_file(self.source).unwrap()
        target_files = [
            target_file.unwrap()
            for target_file in [context.to_schema_file(t) for t in target_schemas]
            if is_successful(target_file) and target_file.unwrap().exists()
        ]
        source_records = load_json_safe(source_file).unwrap()
        target_tokens = {
            item["token"]
            for target_file in target_files
            for item in load_json_safe(target_file).value_or([])
        }
        return [
            Reason(
                f"No reference to '{self.source.value}.{self.reference}': {record[self.reference]}"
            )
            for record in source_records
            if record[self.reference] not in target_tokens
            # NOTE: success if the reference token is "" (0.x) or null (1.0)
            and record[self.reference] not in ("", None)
            and self.is_additional_condition_ok(record)
        ] or None

    def is_additional_condition_ok(self, record: dict[str, Any]) -> bool:
        """Return True if the additional condition is met.

        Args:
            record: The record to check.

        Returns:
            True if the additional condition is met, False otherwise.
        """
        return True


class FileReferenceChecker(Checker):
    """Base class for file reference checkers.

    Attributes:
        name (RuleName): The name of the rule.
        severity (Severity): The severity of the rule.
        description (str): The description of the rule.
        schema (SchemaName): The schema name to check.
    """

    schema: SchemaName

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        filepath = context.to_schema_file(self.schema)
        match filepath:
            case Some(x):
                return Nothing if x.exists() else Maybe.from_value(Reason(f"Missing {x}"))
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))


class ExternalReferenceChecker(Checker):
    """Base class for external reference checks to database tables.

    Attributes:
        name (RuleName): The name of the rule.
        severity (Severity): The severity of the rule.
        description (str): The description of the rule.
        target (SchemaName): The target schema name.
        reference (str): The field name in the target schema (e.g., 'token') to reference.
    """

    target: SchemaName
    reference: str


def missing_references(
    context: SanityContext,
    source: V1SchemaName,
    fields: dict[str, V1SchemaName],
) -> list[Reason]:
    """Return the 1.0 links of a table that refer to no record: one reason per missing token.

    Args:
        context (SanityContext): The sanity context.
        source (V1SchemaName): The table whose records hold the links.
        fields (dict[str, V1SchemaName]): Link field (a token, a list of tokens, or null for no
            link) and the table it refers to.

    Returns:
        A reason per link to a missing record.
    """
    tokens = {
        table: {record.token for record in context.load_records(table).unwrap()}
        for table in set(fields.values())
    }
    reasons = []
    for record in context.load_records(source).unwrap():
        for name, table in fields.items():
            value = getattr(record, name)
            values = value if isinstance(value, list) else [value]
            reasons += [
                Reason(
                    f"{record_name(source)} {record.token}: '{name}' {token} refers to no "
                    f"{record_name(table)}"
                )
                for token in values
                if token is not None and token not in tokens[table]
            ]
    return reasons
