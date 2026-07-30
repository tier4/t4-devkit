from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some

from t4_devkit.lanelet import LaneletParser
from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["REF014"]


@CHECKERS.register()
class REF014(Checker):
    """A checker of REF014."""

    id = RuleID("REF014")
    name = RuleName("traffic-light-to-lanelet")
    severity = Severity.ERROR
    description = "'TrafficLight.primitive_id' refers to a corresponding ID in a lanelet."

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        traffic_light_file = context.to_schema_file(SchemaName.TRAFFIC_LIGHT)
        match traffic_light_file:
            case Some(traffic_light_path):
                if not traffic_light_path.exists():
                    return Maybe.from_value(Reason(f"Missing {SchemaName.TRAFFIC_LIGHT.filename}"))
                return Nothing
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        traffic_light_file = context.to_schema_file(SchemaName.TRAFFIC_LIGHT).unwrap()
        match context.map_dir:
            case Some(map_dir):
                lanelet_path = map_dir.joinpath("lanelet2_map.osm")
            case _:
                return [Reason("Missing 'map' directory path")]

        if not lanelet_path.exists():
            return [Reason(f"Lanelet2 map file not found: {lanelet_path.as_posix()}")]

        traffic_light_records = load_json_safe(traffic_light_file).unwrap()
        traffic_light_ids = _traffic_light_ids(lanelet_path.as_posix())

        return [
            Reason(f"No lanelet relation for 'TrafficLight.primitive_id': {record['primitive_id']}")
            for record in traffic_light_records
            if record["primitive_id"] not in traffic_light_ids
        ] or None


def _traffic_light_ids(lanelet_path: str) -> set[str]:
    """Returns the set of traffic light primitive IDs from the lanelet map."""
    parser = LaneletParser(lanelet_path, verbose=False)

    # Some Lanelet parsers expose way IDs as integers, while primitive_id is stored as a string.
    return {str(way.id) for way in parser.ways.values() if way.tags.get("type") == "traffic_light"}
