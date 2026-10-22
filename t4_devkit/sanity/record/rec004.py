from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, SchemaVersion, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import RecordCountChecker

__all__ = ["REC004"]


@CHECKERS.register()
class REC004(RecordCountChecker):
    """A checker of REC004."""

    id = RuleID("REC004")
    name = RuleName("ego-pose-not-empty")
    severity = Severity.ERROR
    versions = (SchemaVersion.V0, SchemaVersion.V1)
    description = "'EgoPose' record is not empty."
    schema = SchemaName.EGO_POSE

    def check_count(self, records: list[dict]) -> list[Reason] | None:
        num_ego_pose = len(records)
        return [Reason("'EgoPose' record must not be empty")] if num_ego_pose == 0 else None
