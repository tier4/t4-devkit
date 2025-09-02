from __future__ import annotations

from t4_devkit.lanelet import LaneletParser


def test_lanelet_parser(dummy_lanelet_path) -> None:
    """Test `LaneletParser`."""
    _ = LaneletParser(dummy_lanelet_path)
