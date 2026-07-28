from __future__ import annotations

from pathlib import Path

import pytest

from t4_devkit.lanelet import (
    AmbiguousRegulatoryElementError,
    LaneletParser,
    build_linestring_to_regulatory_element_index,
    find_ambiguous_traffic_light_linestrings,
    group_traffic_light_linestrings,
)

_OSM_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="test">
  <node id="1" lat="0.0" lon="0.0"><tag k="local_x" v="0.0"/><tag k="local_y" v="0.0"/></node>
  <node id="2" lat="0.0" lon="0.0"><tag k="local_x" v="1.0"/><tag k="local_y" v="0.0"/></node>
"""

_OSM_FOOTER = "</osm>\n"


def _way(way_id: str) -> str:
    return f'  <way id="{way_id}"><nd ref="1"/><nd ref="2"/></way>\n'


def _regulatory_element(re_id: str, way_ids: list[str], *, subtype: str = "traffic_light") -> str:
    members = "\n".join(
        f'    <member type="way" ref="{way_id}" role="ref_line"/>' for way_id in way_ids
    )
    return (
        f'  <relation id="{re_id}">\n{members}\n'
        f'    <tag k="type" v="regulatory_element"/>\n'
        f'    <tag k="subtype" v="{subtype}"/>\n'
        "  </relation>\n"
    )


def _write_osm(tmp_path: Path, body: str) -> str:
    path = tmp_path / "lanelet2_map.osm"
    path.write_text(_OSM_HEADER + body + _OSM_FOOTER, encoding="utf-8")
    return path.as_posix()


def test_group_traffic_light_linestrings_single_relation(tmp_path: Path) -> None:
    """One traffic-light RE referring to one LineString resolves to one entry."""
    body = _way("400") + _regulatory_element("2000", ["400"])
    parser = LaneletParser(_write_osm(tmp_path, body))

    groups = group_traffic_light_linestrings(parser)

    assert groups == {"400": ["2000"]}


def test_group_traffic_light_linestrings_ignores_non_traffic_light_re(tmp_path: Path) -> None:
    """Regulatory elements with a different subtype (e.g. traffic_sign) are ignored."""
    body = _way("400") + _regulatory_element("2000", ["400"], subtype="traffic_sign")
    parser = LaneletParser(_write_osm(tmp_path, body))

    assert group_traffic_light_linestrings(parser) == {}


def test_build_linestring_to_regulatory_element_index(tmp_path: Path) -> None:
    """Two distinct LineStrings on two distinct REs resolve unambiguously."""
    body = (
        _way("400")
        + _way("401")
        + _regulatory_element("2000", ["400"])
        + _regulatory_element("2001", ["401"])
    )
    parser = LaneletParser(_write_osm(tmp_path, body))

    index = build_linestring_to_regulatory_element_index(parser)

    assert index == {"400": "2000", "401": "2001"}


def test_build_linestring_to_regulatory_element_index_shared_re(tmp_path: Path) -> None:
    """Multiple LineStrings (e.g. multiple lamp heads) may point to the same RE."""
    body = _way("400") + _way("401") + _regulatory_element("2000", ["400", "401"])
    parser = LaneletParser(_write_osm(tmp_path, body))

    index = build_linestring_to_regulatory_element_index(parser)

    assert index == {"400": "2000", "401": "2000"}


def test_build_linestring_to_regulatory_element_index_ambiguous_raises(tmp_path: Path) -> None:
    """A LineString referred to by two REs is ambiguous and must raise."""
    body = (
        _way("400") + _regulatory_element("2000", ["400"]) + _regulatory_element("2001", ["400"])
    )
    parser = LaneletParser(_write_osm(tmp_path, body))

    with pytest.raises(AmbiguousRegulatoryElementError):
        build_linestring_to_regulatory_element_index(parser)


def test_find_ambiguous_traffic_light_linestrings(tmp_path: Path) -> None:
    """`find_ambiguous_traffic_light_linestrings` enumerates without raising."""
    body = (
        _way("400")
        + _way("401")
        + _regulatory_element("2000", ["400"])
        + _regulatory_element("2001", ["400"])
        + _regulatory_element("2002", ["401"])
    )
    parser = LaneletParser(_write_osm(tmp_path, body))

    ambiguous = find_ambiguous_traffic_light_linestrings(parser)

    assert ambiguous == {"400": ["2000", "2001"]}


def test_find_ambiguous_traffic_light_linestrings_empty_when_none(tmp_path: Path) -> None:
    """No ambiguity means an empty mapping, not an error."""
    body = _way("400") + _regulatory_element("2000", ["400"])
    parser = LaneletParser(_write_osm(tmp_path, body))

    assert find_ambiguous_traffic_light_linestrings(parser) == {}
