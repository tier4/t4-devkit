from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity, record_name
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC022"]


@CHECKERS.register()
class REC022(RecordsChecker):
    """A checker of REC022."""

    id = RuleID("REC022")
    name = RuleName("timestamps-microseconds")
    severity = Severity.WARNING
    description = (
        "Timestamps are Unix microseconds: between 2000-01-01 and 2100-01-01 (catches seconds or "
        "nanoseconds)."
    )
    tables = (
        SchemaName.SAMPLE,
        SchemaName.SAMPLE_DATA,
        SchemaName.EGO_POSE,
        SchemaName.VEHICLE_STATE,
        SchemaName.TRAFFIC_LIGHT,
        SchemaName.ROUTE,
        SchemaName.SCENARIO,
        SchemaName.CAPTION,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        # 2000-01-01 and 2100-01-01 in Unix microseconds
        low, high = 946_684_800_000_000, 4_102_444_800_000_000
        fields_of = {
            SchemaName.SAMPLE: ("timestamp",),
            SchemaName.SAMPLE_DATA: ("timestamp",),
            SchemaName.EGO_POSE: ("timestamp",),
            SchemaName.VEHICLE_STATE: ("timestamp",),
            SchemaName.TRAFFIC_LIGHT: ("timestamp",),
            SchemaName.ROUTE: ("valid_from", "valid_until"),
            SchemaName.SCENARIO: ("start_timestamp", "end_timestamp", "key_timestamp"),
            SchemaName.CAPTION: ("start_timestamp", "end_timestamp"),
        }
        failures = []
        for table in self.tables:
            for record in context.load_records(table).unwrap():
                for name in fields_of[table]:
                    value = getattr(record, name)
                    if value is not None and not low <= value < high:
                        failures.append(
                            Reason(f"{record_name(table)} {record.token}: '{name}' {value}")
                        )
        return failures or None
