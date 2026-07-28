from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF015"]


@CHECKERS.register()
class REF015(RecordReferenceChecker):
    """A checker of REF015."""

    id = RuleID("REF015")
    name = RuleName("traffic-light-instance-map-to-instance")
    severity = Severity.ERROR
    description = "'TrafficLightInstanceMap.instance_token' refers to 'Instance' record."
    source = SchemaName.TRAFFIC_LIGHT_INSTANCE_MAP
    target = SchemaName.INSTANCE
    reference = "instance_token"
