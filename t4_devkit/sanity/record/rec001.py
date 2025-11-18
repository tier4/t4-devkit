from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import RecordCountChecker

__all__ = ["REC001"]


@CHECKERS.register()
class REC001(RecordCountChecker):
    """A checker of REC001."""

    id = RuleID("REC001")
    name = RuleName("scene-single")
    severity = Severity.ERROR
    description = "'Scene' record is a single."
    schema = SchemaName.SCENE

    def check_count(self, records: list[dict]) -> list[Reason] | None:
        num_scene = len(records)
        return (
            None
            if num_scene == 1
            else [Reason(f"'Scene' must contain exactly one element: {num_scene}")]
        )
