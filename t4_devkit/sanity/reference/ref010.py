from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName
from ..registry import CHECKERS
from .base import ReferenceChecker

if TYPE_CHECKING:
    pass

__all__ = ["REF010"]


@CHECKERS.register(RuleID("REF010"))
class REF010(ReferenceChecker):
    """A checker of REF010."""

    name = RuleName("instance-to-first-sample-annotation")
    description = "'Instance.first_annotation_token' refers to 'SampleAnnotation' record."
    source = SchemaName.INSTANCE
    target = SchemaName.SAMPLE_ANNOTATION
    reference = "first_annotation_token"
