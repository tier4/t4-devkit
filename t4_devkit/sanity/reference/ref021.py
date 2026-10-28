from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF021"]


@CHECKERS.register()
class REF021(RecordsChecker):
    """A checker of REF021."""

    id = RuleID("REF021")
    name = RuleName("traffic-light-references")
    severity = Severity.ERROR
    description = (
        "'TrafficLight' 'object_ann_token' and 'instance_token' refer to records unless they are "
        "empty."
    )
    tables = (
        SchemaName.INSTANCE,
        SchemaName.OBJECT_ANN,
        SchemaName.TRAFFIC_LIGHT,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        return (
            missing_references(
                context,
                SchemaName.TRAFFIC_LIGHT,
                {"object_ann_token": SchemaName.OBJECT_ANN, "instance_token": SchemaName.INSTANCE},
            )
            or None
        )
