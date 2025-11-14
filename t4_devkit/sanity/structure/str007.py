from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR007"]


@CHECKERS.register()
class STR007(Checker):
    """A checker of STR007."""

    id = RuleID("STR007")
    name = RuleName("schema-file-presence")
    severity = Severity.ERROR
    description = "Mandatory schema JSON files exist under the `annotation/` directory."

    def check(self, context: SanityContext) -> list[Reason] | None:
        failures = []
        for schema in SchemaName:
            match context.to_schema_file(schema):
                case Some(x):
                    if not x.exists() and not schema.is_optional():
                        failures.append(Reason(f"schema file '{schema.filename}' not found"))
                case _:
                    failures.append(Reason(f"schema file '{schema.filename}' not found"))
        return failures if failures else None
