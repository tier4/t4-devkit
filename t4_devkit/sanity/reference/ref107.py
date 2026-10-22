from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity, record_name
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF107"]


@CHECKERS.register()
class REF107(RecordsChecker):
    """A checker of REF107."""

    id = RuleID("REF107")
    name = RuleName("links-mutual")
    severity = Severity.ERROR
    description = (
        "'next' and 'prev' agree: 'A.next' has 'prev' = 'A' ('Sample', 'SampleData', "
        "'SampleAnnotation')."
    )
    tables = (
        SchemaName.SAMPLE,
        SchemaName.SAMPLE_DATA,
        SchemaName.SAMPLE_ANNOTATION,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        failures = []
        for table in self.tables:
            records = {record.token: record for record in context.load_records(table).unwrap()}
            for record in records.values():
                following = records.get(record.next)
                if following is not None and following.prev != record.token:
                    failures.append(
                        Reason(f"{record_name(table)} {record.token}: 'next' has another 'prev'")
                    )
                previous = records.get(record.prev)
                if previous is not None and previous.next != record.token:
                    failures.append(
                        Reason(f"{record_name(table)} {record.token}: 'prev' has another 'next'")
                    )
        return failures or None
