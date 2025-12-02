from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker


@CHECKERS.register()
class REF016(RecordReferenceChecker):
    """A checker of REF016."""

    id = RuleID("REF016")
    name = RuleName("sample-next-to-another")
    severity = Severity.ERROR
    description = "'Sample.next' refers to another one unless it is empty."
    source = SchemaName.SAMPLE
    target = SchemaName.SAMPLE
    reference = "next"
