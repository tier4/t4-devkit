from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC008"]


@CHECKERS.register()
class REC008(RecordsChecker):
    """A checker of REC008."""

    id = RuleID("REC008")
    name = RuleName("sensor-not-empty")
    severity = Severity.ERROR
    description = "'Sensor' record is not empty."
    tables = (SchemaName.SENSOR,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        if not context.load_records(SchemaName.SENSOR).unwrap():
            return [Reason("'Sensor' record must not be empty")]
        return None
