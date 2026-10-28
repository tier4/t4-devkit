from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF023"]


@CHECKERS.register()
class REF023(RecordsChecker):
    """A checker of REF023."""

    id = RuleID("REF023")
    name = RuleName("scenario-references")
    severity = Severity.ERROR
    description = "'Scenario.log_token' refers to 'Log' record."
    tables = (
        SchemaName.LOG,
        SchemaName.SCENARIO,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(context, SchemaName.SCENARIO, {"log_token": SchemaName.LOG}) or None
        )
