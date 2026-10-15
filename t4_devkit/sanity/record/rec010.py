from __future__ import annotations

from typing import TYPE_CHECKING

from collections import Counter

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC010"]


@CHECKERS.register()
class REC010(RecordsChecker):
    """A checker of REC010."""

    id = RuleID("REC010")
    name = RuleName("instance-index-unique")
    severity = Severity.ERROR
    description = "'Instance.index' values are unique where set."
    tables = (SchemaName.INSTANCE,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        counts = Counter(
            instance.index
            for instance in context.load_records(SchemaName.INSTANCE).unwrap()
            if instance.index is not None
        )
        return [
            Reason(f"'Instance.index' {index} is used by {count} instances")
            for index, count in sorted(counts.items())
            if count > 1
        ] or None
