from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from .base import declared_capabilities, present_capabilities

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC023"]


@CHECKERS.register()
class REC023(RecordsChecker):
    """A checker of REC023."""

    id = RuleID("REC023")
    name = RuleName("capabilities-present")
    severity = Severity.ERROR
    description = (
        "Everything 'manifest.json' 'capabilities' declares is present: channels, map, tables and "
        "the labels of its tasks."
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
        present = present_capabilities(context)
        return [
            Reason(f"Declared but not present: {item}")
            for item in sorted(declared_capabilities(context) - present)
        ] or None
