from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import RecordReferenceChecker


__all__ = ["REF009"]


@CHECKERS.register(RuleID("REF009"))
class REF009(RecordReferenceChecker):
    """A checker of REF009."""

    name = RuleName("instance-to-category")
    description = "'Instance.category_token' refers to 'Category' record."
    source = SchemaName.INSTANCE
    target = SchemaName.CATEGORY
    reference = "category_token"
