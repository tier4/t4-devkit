from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT037"]


@CHECKERS.register()
class FMT037(TableFieldChecker):
    """A checker of FMT037."""

    id = RuleID("FMT037")
    name = RuleName("traffic-light-field")
    severity = Severity.ERROR
    description = "All 'TrafficLight' records are valid."
    table = SchemaName.TRAFFIC_LIGHT
