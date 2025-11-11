from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT014"]


@CHECKERS.register(RuleID("FMT014"))
class FMT014(FieldTypeChecker):
    """A checker of FMT014."""

    name = RuleName("lidarseg-field")
    severity = Severity.ERROR
    description = "All types of 'LidarSeg' fields are valid."
    schema = SchemaName.LIDARSEG
