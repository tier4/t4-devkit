from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from .base import RecordCountChecker


__all__ = ["REC003"]


@CHECKERS.register(RuleID("REC003"))
class REC003(RecordCountChecker):
    """A checker of REC003."""

    name = RuleName("sample-data-not-empty")
    description = "'SampleData' record is not empty."
    schema = SchemaName.SAMPLE_DATA

    def check_count(self, records: list[dict]) -> list[Reason]:
        num_sample_data = len(records)
        return [Reason("'SampleData' record must not be empty")] if num_sample_data == 0 else []
