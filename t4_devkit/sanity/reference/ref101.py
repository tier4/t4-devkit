from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF101"]


@CHECKERS.register()
class REF101(RecordReferenceChecker):
    """A checker of REF101."""

    id = RuleID("REF101")
    name = RuleName("sample-next-to-another")
    severity = Severity.ERROR
    description = "'Sample.next' refers to another one unless it is empty."
    source = SchemaName.SAMPLE
    target = SchemaName.SAMPLE
    reference = "next"
