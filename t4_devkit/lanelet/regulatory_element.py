from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parser import LaneletParser

__all__ = [
    "AmbiguousRegulatoryElementError",
    "build_linestring_to_regulatory_element_index",
    "find_ambiguous_traffic_light_linestrings",
    "group_traffic_light_linestrings",
]

# Relation member roles under which a Lanelet2 `regulatory_element` refers to the
# LineString representing a traffic-light lamp geometry.
_TRAFFIC_LIGHT_REF_ROLES = ("ref_line", "refers")


class AmbiguousRegulatoryElementError(ValueError):
    """Raised when a traffic-light LineString is referred to by more than one
    Regulatory Element.

    The relation from a LineString to its owning Regulatory Element must be
    unique so that `object_ann.instance_token -> traffic_light_linestring_id`
    resolves to exactly one Regulatory Element ID. Silently picking one of
    several candidates would hide a map authoring problem, so this is raised
    instead of resolved implicitly.
    """


def group_traffic_light_linestrings(parser: LaneletParser) -> dict[str, list[str]]:
    """Group traffic-light LineString IDs by every Regulatory Element that refers to them.

    This is the raw (non-validating) relation walk shared by
    `build_linestring_to_regulatory_element_index` and
    `find_ambiguous_traffic_light_linestrings`, and by validation tooling that needs to
    tell apart "LineString not referred to by any Regulatory Element" from "LineString
    referred to by more than one".

    Args:
        parser (LaneletParser): Parsed Lanelet2 OSM map.

    Returns:
        Mapping from LineString ID (way ID, as string) to the sorted list of Regulatory
        Element IDs that refer to it. A LineString with exactly one entry is
        unambiguous; more than one is ambiguous; a LineString absent from this mapping
        is not referred to by any traffic-light Regulatory Element.
    """
    linestring_to_re_ids: dict[str, set[str]] = {}

    for relation in parser.relations.values():
        if relation.tags.get("type") != "regulatory_element":
            continue
        if "traffic_light" not in relation.tags.get("subtype", ""):
            continue

        for member in relation.members:
            if member.type == "way" and member.role in _TRAFFIC_LIGHT_REF_ROLES:
                linestring_to_re_ids.setdefault(member.ref, set()).add(relation.id)

    return {
        linestring_id: sorted(re_ids) for linestring_id, re_ids in linestring_to_re_ids.items()
    }


def find_ambiguous_traffic_light_linestrings(parser: LaneletParser) -> dict[str, list[str]]:
    """Find all traffic-light LineStrings referred to by more than one Regulatory Element.

    Unlike `build_linestring_to_regulatory_element_index`, this never raises: it is meant
    for validation tooling that enumerates every issue in a map instead of stopping at the
    first one (see sanity checkers, which report ambiguous relations rather than raising).

    Args:
        parser (LaneletParser): Parsed Lanelet2 OSM map.

    Returns:
        Mapping from LineString ID to the sorted list of Regulatory Element IDs that
        refer to it, for every LineString referred to by more than one. Empty if there
        is no ambiguity.
    """
    return {
        linestring_id: re_ids
        for linestring_id, re_ids in group_traffic_light_linestrings(parser).items()
        if len(re_ids) > 1
    }


def build_linestring_to_regulatory_element_index(parser: LaneletParser) -> dict[str, str]:
    """Build a reverse index from traffic-light LineString ID to Regulatory Element ID.

    Walks every `regulatory_element` relation in the Lanelet2 map whose `subtype` tag
    contains `"traffic_light"`, and indexes the way (LineString) IDs it refers to
    (member role `"ref_line"` or `"refers"`) by the relation's own ID.

    This is the single, shared implementation of the Lanelet2-side half of the relation

        traffic_light.json: instance_token -> traffic_light_linestring_id
        (this function):    traffic_light_linestring_id -> Regulatory Element ID

    so that consumers (e.g. `perception_eval`) do not need to re-implement Lanelet2
    parsing to resolve Regulatory Element IDs.

    Args:
        parser (LaneletParser): Parsed Lanelet2 OSM map.

    Returns:
        Mapping from LineString ID (way ID, as string) to Regulatory Element ID
        (relation ID, as string).

    Raises:
        AmbiguousRegulatoryElementError: If a LineString is referred to by more than
            one traffic-light Regulatory Element. Use `find_ambiguous_traffic_light_linestrings`
            instead if you need to enumerate every ambiguous LineString rather than fail
            on the first one.
    """
    linestring_to_re_ids = group_traffic_light_linestrings(parser)

    linestring_to_re_id: dict[str, str] = {}
    for linestring_id, re_ids in linestring_to_re_ids.items():
        if len(re_ids) > 1:
            raise AmbiguousRegulatoryElementError(
                f"LineString '{linestring_id}' is referenced by multiple traffic-light "
                f"Regulatory Elements: {re_ids}. Each traffic-light LineString must "
                "resolve to exactly one Regulatory Element."
            )
        linestring_to_re_id[linestring_id] = re_ids[0]

    return linestring_to_re_id
