from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF302"]


@CHECKERS.register()
class REF302(RecordsChecker):
    """A checker of REF302."""

    id = RuleID("REF302")
    name = RuleName("instance-to-map-element")
    severity = Severity.ERROR
    description = "'Instance.map_element' refers to an element of its 'type' in the lanelet2 map."
    tables = (
        SchemaName.MAP,
        SchemaName.INSTANCE,
    )

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match super().can_skip(context):
            case Some(reason):
                return Some(reason)
        match context.lanelet_map:
            case Some(_):
                return Nothing
            case _:
                return Maybe.from_value(Reason("No lanelet2 map to check against"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        lanelet = context.lanelet_map.unwrap()
        elements = {
            "node": set(lanelet.nodes),
            "way": set(lanelet.ways),
            "relation": set(lanelet.relations),
        }
        return [
            Reason(f"Instance {instance.token}: no {element.type.value} {element.id} in the map")
            for instance in context.load_records(SchemaName.INSTANCE).unwrap()
            if (element := instance.map_element).id is not None
            and str(element.id) not in elements[element.type.value]
        ] or None
