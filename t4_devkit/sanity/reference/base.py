from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful

from ..checker import Checker
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from t4_devkit.schema import SchemaName

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
        target_tokens = [
            item["token"]
            for target_file in target_files
            for item in load_json_safe(target_file).unwrap()
        ]
        return [
            Reason(
                f"No reference to '{self.source.value}.{self.reference}': {record[self.reference]}"
            )
            for record in source_records
            if record[self.reference] not in target_tokens
            and record[self.reference] != ""  # NOTE: success if the reference token is ""
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
