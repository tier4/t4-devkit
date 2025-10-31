from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import ReferenceChecker


__all__ = ["REF002"]


@CHECKERS.register(RuleID("REF002"))
class REF002(ReferenceChecker):
    """A checker of REF002."""

    name = RuleName("scene-to-first-sample")
    description = "'Scene.first_sample_token' refers to 'Sample' record."
    source = SchemaName.SCENE
    target = SchemaName.SAMPLE
    reference = "first_sample_token"
