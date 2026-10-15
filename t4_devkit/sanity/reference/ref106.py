from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, SchemaVersion, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF106"]


@CHECKERS.register()
class REF106(RecordReferenceChecker):
    """A checker of REF106."""

    id = RuleID("REF106")
    name = RuleName("sample-data-prev-to-another")
    severity = Severity.ERROR
    versions = (SchemaVersion.V0, SchemaVersion.V1)
    description = "'SampleData.prev' refers to another one unless it is empty."
    source = SchemaName.SAMPLE_DATA
    target = SchemaName.SAMPLE_DATA
    reference = "prev"
