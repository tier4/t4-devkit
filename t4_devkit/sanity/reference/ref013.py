from __future__ import annotations

from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import RecordReferenceChecker

__all__ = ["REF013"]


@CHECKERS.register()
class REF013(RecordReferenceChecker):
    """A checker of REF013."""

    id = RuleID("REF013")
    name = RuleName("traffic-light-to-instance")
    severity = Severity.ERROR
    description = "'TrafficLight.instance_token' refers to 'Instance' record."
    source = SchemaName.TRAFFIC_LIGHT
    target = SchemaName.INSTANCE
    reference = "instance_token"
