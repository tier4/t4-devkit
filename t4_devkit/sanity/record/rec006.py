from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from .base import RecordCountChecker


__all__ = ["REC006"]


@CHECKERS.register(RuleID("REC006"))
class REC006(RecordCountChecker):
    """A checker of REC006."""

    name = RuleName("instance-not-empty")
    description = "'Instance' record is not empty."
    schema = SchemaName.INSTANCE

    def check_count(self, records: list[dict]) -> list[Reason]:
        num_instance = len(records)
        return [Reason("'Instance' record must not be empty")] if num_instance == 0 else []
