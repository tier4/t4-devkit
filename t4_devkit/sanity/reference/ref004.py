from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import ReferenceChecker

if TYPE_CHECKING:
    pass

__all__ = ["REF004"]


@CHECKERS.register(RuleID("REF004"))
class REF004(ReferenceChecker):
    """A checker of REF004."""

    name = RuleName("sample-to-scene")
    description = "'Sample.scene_token' refers to 'Scene' record."
    source = SchemaName.SAMPLE
    target = SchemaName.SCENE
    reference = "scene_token"
