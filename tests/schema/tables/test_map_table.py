from t4_devkit.schema import Map


def test_map_json(map_json) -> None:
    """Test loading map from a json file."""
    _ = Map.from_json(map_json)


def test_map(map_dict) -> None:
    """Test loading map from a dictionary."""
    _ = Map.from_dict(map_dict)
