from __future__ import annotations

from t4_devkit.schema.v1 import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from .base import TableFieldChecker

__all__ = ["FMT024"]


@CHECKERS.register()
class FMT024(TableFieldChecker):
    """A checker of FMT024."""

    id = RuleID("FMT024")
    name = RuleName("sensor-field")
    severity = Severity.ERROR
    description = (
        "All 'Sensor' records are valid, including exactly one modality block, matching 'modality'."
    )
    table = SchemaName.SENSOR
