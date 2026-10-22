from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF015"]


@CHECKERS.register()
class REF015(RecordsChecker):
    """A checker of REF015."""

    id = RuleID("REF015")
    name = RuleName("sample-data-to-sensor")
    severity = Severity.ERROR
    description = "'SampleData.sensor_token' refers to 'Sensor' record."
    tables = (
        SchemaName.SAMPLE_DATA,
        SchemaName.SENSOR,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(context, SchemaName.SAMPLE_DATA, {"sensor_token": SchemaName.SENSOR})
            or None
        )
