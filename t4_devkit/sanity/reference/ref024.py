from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF024"]


@CHECKERS.register()
class REF024(RecordsChecker):
    """A checker of REF024."""

    id = RuleID("REF024")
    name = RuleName("caption-references")
    severity = Severity.ERROR
    description = (
        "'Caption' 'log_token', 'sample_data_token', 'scenario_token' and 'instance_tokens' refer "
        "to records unless they are empty."
    )
    tables = (
        SchemaName.CAPTION,
        SchemaName.INSTANCE,
        SchemaName.LOG,
        SchemaName.SAMPLE_DATA,
        SchemaName.SCENARIO,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(
                context,
                SchemaName.CAPTION,
                {
                    "log_token": SchemaName.LOG,
                    "sample_data_token": SchemaName.SAMPLE_DATA,
                    "scenario_token": SchemaName.SCENARIO,
                    "instance_tokens": SchemaName.INSTANCE,
                },
            )
            or None
        )
