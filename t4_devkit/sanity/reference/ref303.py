from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF303"]


@CHECKERS.register()
class REF303(RecordsChecker):
    """A checker of REF303."""

    id = RuleID("REF303")
    name = RuleName("traffic-light-to-lanelet")
    severity = Severity.ERROR
    description = (
        "'TrafficLight.regulatory_element_id' is a traffic-light regulatory element of the "
        "lanelet2 map."
    )
    tables = (
        SchemaName.MAP,
        SchemaName.TRAFFIC_LIGHT,
    )

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        skip = super().can_skip(context)
        if skip != Nothing:
            return skip
        if context.lanelet_map == Nothing:
            return Maybe.from_value(Reason("No lanelet2 map to check against"))
        return Nothing

    def check(self, context: SanityContext) -> list[Reason] | None:
        regulatory_elements = {
            id
            for id, relation in context.lanelet_map.unwrap().relations.items()
            if relation.tags.get("type") == "regulatory_element"
            and relation.tags.get("subtype") == "traffic_light"
        }
        return [
            Reason(
                f"TrafficLight {light.token}: no traffic-light regulatory element {light.regulatory_element_id}"
            )
            for light in context.load_records(SchemaName.TRAFFIC_LIGHT).unwrap()
            if str(light.regulatory_element_id) not in regulatory_elements
        ] or None
