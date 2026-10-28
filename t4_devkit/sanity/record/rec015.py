from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC015"]


@CHECKERS.register()
class REC015(RecordsChecker):
    """A checker of REC015."""

    id = RuleID("REC015")
    name = RuleName("orientation-number-allowed")
    severity = Severity.ERROR
    description = (
        "'ObjectAnn.orientation' / 'number' are set only for categories with "
        "'has_orientation' / 'has_number'."
    )
    tables = (
        SchemaName.CATEGORY,
        SchemaName.OBJECT_ANN,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        categories = {
            category.token: category
            for category in context.load_records(SchemaName.CATEGORY).unwrap()
        }
        failures = []
        for ann in context.load_records(SchemaName.OBJECT_ANN).unwrap():
            category = categories.get(ann.category_token)
            if category is None:
                continue  # reported by the reference rules
            if ann.orientation is not None and not category.has_orientation:
                failures.append(Reason(f"ObjectAnn {ann.token}: 'orientation' for {category.name}"))
            if ann.number is not None and not category.has_number:
                failures.append(Reason(f"ObjectAnn {ann.token}: 'number' for {category.name}"))
        return failures or None
