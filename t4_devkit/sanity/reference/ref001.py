from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF001"]


@CHECKERS.register()
class REF001(RecordReferenceChecker):
    """A checker of REF001."""

    id = RuleID("REF001")
    name = RuleName("scene-to-log")
    severity = Severity.ERROR
    description = "'Scene.log_token' refers to 'Log' record."
    source = SchemaName.SCENE
    target = SchemaName.LOG
    reference = "log_token"
