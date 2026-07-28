from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some

from t4_devkit.lanelet import LaneletParser, group_traffic_light_linestrings
from t4_devkit.schema import SchemaName

from ..checker import RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe
from .base import ExternalReferenceChecker

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["REF016"]


@CHECKERS.register()
class REF016(ExternalReferenceChecker):
    """A checker of REF016."""

    id = RuleID("REF016")
    name = RuleName("traffic-light-instance-map-linestring-to-regulatory-element")
    severity = Severity.ERROR
    description = (
        "'TrafficLightInstanceMap.traffic_light_linestring_id' exists in the Lanelet2 "
        "map and resolves to exactly one traffic-light Regulatory Element."
    )
    target = SchemaName.MAP
    reference = "filename"

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        tl_file = context.to_schema_file(SchemaName.TRAFFIC_LIGHT_INSTANCE_MAP)
        map_file = context.to_schema_file(SchemaName.MAP)
        match (tl_file, map_file):
            case Some(x), Some(y):
                if not x.exists():
                    return Maybe.from_value(
                        Reason(f"Missing {SchemaName.TRAFFIC_LIGHT_INSTANCE_MAP.filename}")
                    )
                if not y.exists():
                    return Maybe.from_value(Reason(f"Missing {SchemaName.MAP.filename}"))
                return Nothing
            case _:
                return Maybe.from_value(Reason("Missing 'annotation' directory path"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        """Check every `traffic_light_linestring_id` against the Lanelet2 map.

        Reports, for each distinct `traffic_light_linestring_id` used in
        `traffic_light_instance_map.json`: the LineString missing from the map, the
        LineString not referred to by any traffic-light Regulatory Element, or the
        LineString referred to by more than one (ambiguous). All issues are enumerated
        rather than stopping at the first one.

        Args:
            context: The sanity check context containing schema files and data root.

        Returns:
            List of Reason objects for invalid relations, or None if all are valid.
        """
        tl_filepath = context.to_schema_file(SchemaName.TRAFFIC_LIGHT_INSTANCE_MAP).unwrap()
        map_filepath = context.to_schema_file(SchemaName.MAP).unwrap()
        data_root = context.data_root.unwrap()

        tl_records = load_json_safe(tl_filepath).unwrap()
        map_records = load_json_safe(map_filepath).unwrap()

        if not map_records:
            return [Reason("'map' record is missing; cannot resolve Regulatory Elements")]

        map_path = data_root.joinpath(map_records[0]["filename"])
        if not map_path.exists():
            return [Reason(f"Map file not found: {map_path.as_posix()}")]

        parser = LaneletParser(map_path.as_posix())
        groups = group_traffic_light_linestrings(parser)

        linestring_ids = sorted(
            {str(record["traffic_light_linestring_id"]) for record in tl_records}
        )

        reasons: list[Reason] = []
        for linestring_id in linestring_ids:
            if linestring_id not in parser.ways:
                reasons.append(
                    Reason(f"LineString '{linestring_id}' does not exist in the map")
                )
                continue

            re_ids = groups.get(linestring_id)
            if not re_ids:
                reasons.append(
                    Reason(
                        f"LineString '{linestring_id}' is not referenced by any "
                        "traffic-light Regulatory Element"
                    )
                )
            elif len(re_ids) > 1:
                reasons.append(
                    Reason(
                        f"LineString '{linestring_id}' is referenced by multiple "
                        f"Regulatory Elements: {re_ids}"
                    )
                )

        return reasons or None
