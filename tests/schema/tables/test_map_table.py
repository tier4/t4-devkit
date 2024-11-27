from t4_devkit.schema import Map


def test_map_json(map_json) -> None:
    """Test loading map from a json file."""
    _ = Map.from_json(map_json)


def test_map(map_dict) -> None:
    """Test loading map from a dictionary."""
    _ = Map.from_dict(map_dict)


def test_new_map(map_dict) -> None:
    """Test generating map with a new token."""
    without_token = {k: v for k, v in map_dict.items() if k != "token"}
    ret = Map.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != map_dict["token"]
