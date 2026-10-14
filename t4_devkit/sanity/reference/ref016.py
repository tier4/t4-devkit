from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF016"]


@CHECKERS.register()
class REF016(RecordsChecker):
    """A checker of REF016."""

    id = RuleID("REF016")
    name = RuleName("log-to-vehicle")
    severity = Severity.ERROR
    description = "'Log.vehicle_token' refers to 'Vehicle' record."
    tables = (
        SchemaName.LOG,
        SchemaName.VEHICLE,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(context, SchemaName.LOG, {"vehicle_token": SchemaName.VEHICLE})
            or None
        )
