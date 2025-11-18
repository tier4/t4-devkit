from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF003"]


@CHECKERS.register()
class REF003(RecordReferenceChecker):
    """A checker of REF003."""

    id = RuleID("REF003")
    name = RuleName("scene-to-last-sample")
    severity = Severity.ERROR
    description = "'Scene.last_sample_token' refers to 'Sample' record."
    source = SchemaName.SCENE
    target = SchemaName.SAMPLE
    reference = "last_sample_token"
