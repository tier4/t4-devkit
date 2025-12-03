from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF106"]


@CHECKERS.register()
class REF106(RecordReferenceChecker):
    """A checker of REF106."""

    id = RuleID("REF106")
    name = RuleName("sample-data-prev-to-another")
    severity = Severity.ERROR
    description = "'SampleData.prev' refers to another one unless it is empty."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.SAMPLE_DATA
    reference = "prev"
