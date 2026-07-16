from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import FieldTypeChecker

__all__ = ["FMT019"]


@CHECKERS.register()
class FMT019(FieldTypeChecker):
    """A checker of FMT019."""

    id = RuleID("FMT019")
    name = RuleName("traffic-light-field")
    severity = Severity.ERROR
    description = "All types of 'TrafficLight' fields are valid."
    schema = SchemaName.TRAFFIC_LIGHT
