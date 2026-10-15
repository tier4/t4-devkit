from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF020"]


@CHECKERS.register()
class REF020(RecordsChecker):
    """A checker of REF020."""

    id = RuleID("REF020")
    name = RuleName("keypoint-references")
    severity = Severity.ERROR
    description = (
        "'Keypoint' 'sample_data_token', 'instance_token' and 'category_tokens' refer to records."
    )
    tables = (
        SchemaName.CATEGORY,
        SchemaName.INSTANCE,
        SchemaName.KEYPOINT,
        SchemaName.SAMPLE_DATA,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(
                context,
                SchemaName.KEYPOINT,
                {
                    "sample_data_token": SchemaName.SAMPLE_DATA,
                    "instance_token": SchemaName.INSTANCE,
                    "category_tokens": SchemaName.CATEGORY,
                },
            )
            or None
        )
