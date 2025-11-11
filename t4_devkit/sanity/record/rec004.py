from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from .base import RecordCountChecker


__all__ = ["REC004"]


@CHECKERS.register(RuleID("REC004"))
class REC004(RecordCountChecker):
    """A checker of REC004."""

    name = RuleName("ego-pose-not-empty")
    description = "'EgoPose' record is not empty."
    schema = SchemaName.EGO_POSE

    def check_count(self, records: list[dict]) -> list[Reason]:
        num_ego_pose = len(records)
        return [Reason("'EgoPose' record must not be empty")] if num_ego_pose == 0 else []
