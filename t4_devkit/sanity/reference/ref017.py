from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker


@CHECKERS.register()
class REF017(RecordReferenceChecker):
    """A checker of REF017."""

    id = RuleID("REF017")
    name = RuleName("sample-prev-to-another")
    severity = Severity.ERROR
    description = "'Sample.prev' refers to another one unless it is empty."
    source = SchemaName.SAMPLE
    target = SchemaName.SAMPLE
    reference = "prev"
