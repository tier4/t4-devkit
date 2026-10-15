from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF022"]


@CHECKERS.register()
class REF022(RecordsChecker):
    """A checker of REF022."""

    id = RuleID("REF022")
    name = RuleName("route-references")
    severity = Severity.ERROR
    description = "'Route' 'log_token' and 'map_token' refer to records."
    tables = (
        SchemaName.LOG,
        SchemaName.MAP,
        SchemaName.ROUTE,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(
                context,
                SchemaName.ROUTE,
                {"log_token": SchemaName.LOG, "map_token": SchemaName.MAP},
            )
            or None
        )
