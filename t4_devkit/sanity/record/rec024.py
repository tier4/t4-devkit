from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from .base import declared_capabilities, present_capabilities

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC024"]


@CHECKERS.register()
class REC024(RecordsChecker):
    """A checker of REC024."""

    id = RuleID("REC024")
    name = RuleName("capabilities-complete")
    severity = Severity.WARNING
    description = (
        "Everything present is declared in 'capabilities': the same checks as REC023, the other "
        "way round."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.SAMPLE_DATA,
        SchemaName.MAP,
        SchemaName.ROUTE,
        SchemaName.TRAFFIC_LIGHT,
        SchemaName.VEHICLE_STATE,
        SchemaName.SCENARIO,
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.OBJECT_ANN,
        SchemaName.CATEGORY,
        SchemaName.KEYPOINT,
        SchemaName.INSTANCE,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        declared = declared_capabilities(context)
        return [
            Reason(f"Present but not declared: {item}")
            for item in sorted(present_capabilities(context) - declared)
        ] or None
