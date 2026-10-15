from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF018"]


@CHECKERS.register()
class REF018(RecordsChecker):
    """A checker of REF018."""

    id = RuleID("REF018")
    name = RuleName("sample-annotation-references")
    severity = Severity.ERROR
    description = (
        "'SampleAnnotation' 'sample_token', 'instance_token', 'attribute_tokens' and "
        "'visibility_token' (unless empty) refer to records."
    )
    tables = (
        SchemaName.ATTRIBUTE,
        SchemaName.INSTANCE,
        SchemaName.SAMPLE,
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.VISIBILITY,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(
                context,
                SchemaName.SAMPLE_ANNOTATION,
                {
                    "sample_token": SchemaName.SAMPLE,
                    "instance_token": SchemaName.INSTANCE,
                    "attribute_tokens": SchemaName.ATTRIBUTE,
                    "visibility_token": SchemaName.VISIBILITY,
                },
            )
            or None
        )
