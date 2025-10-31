from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import ReferenceChecker


__all__ = ["REF001"]


@CHECKERS.register(RuleID("REF001"))
class REF001(ReferenceChecker):
    """A checker of REF001."""

    name = RuleName("scene-to-log")
    description = "'Scene.log_token' refers to 'Log' record."
    source = SchemaName.SCENE
    target = SchemaName.LOG
    reference = "log_token"
