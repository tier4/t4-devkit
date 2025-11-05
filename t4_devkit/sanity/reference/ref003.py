from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import RecordReferenceChecker


__all__ = ["REF003"]


@CHECKERS.register(RuleID("REF003"))
class REF003(RecordReferenceChecker):
    """A checker of REF003."""

    name = RuleName("scene-to-last-sample")
    description = "'Scene.last_sample_token' refers to 'Sample' record."
    source = SchemaName.SCENE
    target = SchemaName.SAMPLE
    reference = "last_sample_token"
