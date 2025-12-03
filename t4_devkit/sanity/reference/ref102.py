from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF102"]


@CHECKERS.register()
class REF102(RecordReferenceChecker):
    """A checker of REF102."""

    id = RuleID("REF102")
    name = RuleName("sample-prev-to-another")
    severity = Severity.ERROR
    description = "'Sample.prev' refers to another one unless it is empty."
    source = SchemaName.SAMPLE
    target = SchemaName.SAMPLE
    reference = "prev"
