from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF004"]


@CHECKERS.register()
class REF004(RecordReferenceChecker):
    """A checker of REF004."""

    id = RuleID("REF004")
    name = RuleName("sample-to-scene")
    severity = Severity.ERROR
    description = "'Sample.scene_token' refers to 'Scene' record."
    source = SchemaName.SAMPLE
    target = SchemaName.SCENE
    reference = "scene_token"
