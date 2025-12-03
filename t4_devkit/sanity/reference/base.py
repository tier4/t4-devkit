from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.maybe import Maybe, Nothing, Some

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
        target (SchemaName): The target schema name.
        reference (str): The reference token name in the source record.
    """

    source: SchemaName
    target: SchemaName
    reference: str

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        source_file = context.to_schema_file(self.source)
        target_file = context.to_schema_file(self.target)
        match (source_file, target_file):
            case Some(x), Some(y):
                if not x.exists():
                    return Maybe.from_value(Reason(f"Missing {self.source.filename}"))
                elif not y.exists():
                    return Maybe.from_value(Reason(f"Missing {self.target.filename}"))
                else:
                    return Nothing
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        source_file = context.to_schema_file(self.source).unwrap()
        target_file = context.to_schema_file(self.target).unwrap()
        source_records = load_json_safe(source_file).unwrap()
        target_tokens = [item["token"] for item in load_json_safe(target_file).unwrap()]
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
        reference (str): The reference token name in the target record.
    """
    target: SchemaName
    reference: str