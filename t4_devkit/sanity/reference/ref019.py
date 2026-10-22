from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF019"]


@CHECKERS.register()
class REF019(RecordsChecker):
    """A checker of REF019."""

    id = RuleID("REF019")
    name = RuleName("object-ann-references")
    severity = Severity.ERROR
    description = (
        "'ObjectAnn' 'sample_data_token', 'instance_token' (unless empty), 'category_token' and "
        "'attribute_tokens' refer to records."
    )
    tables = (
        SchemaName.ATTRIBUTE,
        SchemaName.CATEGORY,
        SchemaName.INSTANCE,
        SchemaName.OBJECT_ANN,
        SchemaName.SAMPLE_DATA,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(
                context,
                SchemaName.OBJECT_ANN,
                {
                    "sample_data_token": SchemaName.SAMPLE_DATA,
                    "instance_token": SchemaName.INSTANCE,
                    "category_token": SchemaName.CATEGORY,
                    "attribute_tokens": SchemaName.ATTRIBUTE,
                },
            )
            or None
        )
