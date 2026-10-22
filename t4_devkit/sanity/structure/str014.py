from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import ManifestChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR014"]


@CHECKERS.register()
class STR014(ManifestChecker):
    """A checker of STR014."""

    id = RuleID("STR014")
    name = RuleName("manifest-required-tables")
    severity = Severity.ERROR
    description = "'manifest.json' lists every required table."

    def check(self, context: SanityContext) -> list[Reason] | None:
        tables = context.manifest.unwrap().tables
        return [
            Reason(f"Required table not listed: {table.value}")
            for table in SchemaName
            if not table.is_optional() and table.value not in tables
        ] or None
