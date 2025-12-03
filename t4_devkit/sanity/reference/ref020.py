from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker


@CHECKERS.register()
class REF020(RecordReferenceChecker):
    """A checker of REF020."""

    id = RuleID("REF020")
    name = RuleName("sample-data-next-to-another")
    severity = Severity.ERROR
    description = "'SampleData.next' refers to another one unless it is empty."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.SAMPLE_DATA
    reference = "next"
