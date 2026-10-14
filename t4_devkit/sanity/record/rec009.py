from __future__ import annotations

from typing import TYPE_CHECKING

from collections import Counter

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC009"]


@CHECKERS.register()
class REC009(RecordsChecker):
    """A checker of REC009."""

    id = RuleID("REC009")
    name = RuleName("sensor-index-unique")
    severity = Severity.ERROR
    description = "'Sensor.index' values are unique."
    tables = (SchemaName.SENSOR,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        counts = Counter(
            sensor.index for sensor in context.load_records(SchemaName.SENSOR).unwrap()
        )
        return [
            Reason(f"'Sensor.index' {index} is used by {count} sensors")
            for index, count in sorted(counts.items())
            if count > 1
        ] or None
