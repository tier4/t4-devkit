from __future__ import annotations

from typing_extensions import Any

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF005"]


@CHECKERS.register(RuleID("REF005"))
class REF005(RecordReferenceChecker):
    """A checker of REF005."""

    name = RuleName("sample-data-to-sample")
    severity = Severity.ERROR
    description = "'SampleData.sample_token' refers to 'Sample' record."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.SAMPLE
    reference = "sample_token"

    def is_additional_condition_ok(self, record: dict[str, Any]) -> bool:
        return record["is_valid"]
