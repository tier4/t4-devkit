from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from .base import RecordCountChecker


__all__ = ["REC002"]


@CHECKERS.register(RuleID("REC002"))
class REC002(RecordCountChecker):
    """A checker of REC002."""

    name = RuleName("sample-not-empty")
    description = "'Sample' record is not empty."
    schema = SchemaName.SAMPLE

    def check_count(self, records: list[dict]) -> list[Reason]:
        num_sample = len(records)
        return [Reason("'Sample' record must not be empty")] if num_sample == 0 else []
