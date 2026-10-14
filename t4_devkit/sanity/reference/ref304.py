from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF304"]


@CHECKERS.register()
class REF304(RecordsChecker):
    """A checker of REF304."""

    id = RuleID("REF304")
    name = RuleName("route-to-lanelet")
    severity = Severity.ERROR
    description = "'Route' segment ids are lanelets of the lanelet2 map."
    tables = (
        SchemaName.MAP,
        SchemaName.ROUTE,
    )

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        skip = super().can_skip(context)
        if skip != Nothing:
            return skip
        if context.lanelet_map == Nothing:
            return Maybe.from_value(Reason("No lanelet2 map to check against"))
        return Nothing

    def check(self, context: SanityContext) -> list[Reason] | None:
        lanelets = {
            id
            for id, relation in context.lanelet_map.unwrap().relations.items()
            if relation.tags.get("type") == "lanelet"
        }
        return [
            Reason(f"Route {route.token}: no lanelet {id}")
            for route in context.load_records(SchemaName.ROUTE).unwrap()
            for segment in route.segments
            for id in sorted({segment.preferred_primitive_id, *segment.primitive_ids})
            if str(id) not in lanelets
        ] or None
