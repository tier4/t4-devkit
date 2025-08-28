from __future__ import annotations

from t4_devkit.lanelet import LaneletParser


def test_lanelet_parser() -> None:
    """Test `LaneletParser`."""
    lanelet_path = "tests/sample/map/lanelet2_map.osm"
    _ = LaneletParser(lanelet_path)
