from t4_devkit.schema import Visibility, VisibilityLevel, serialize_schema, serialize_schemas


def test_visibility_level() -> None:
    """Test VisibilityLevel."""

    levels = ("full", "most", "partial", "none", "unavailable")

    # check all enum members are covered by above names
    members: list[str] = [m.value for m in VisibilityLevel]
    assert set(members) == set(levels)

    # check each member can construct
    for value in levels:
        _ = VisibilityLevel(value)


def test_visibility_level_deprecated() -> None:
    """Test VisibilityLevel with deprecated format."""

    levels = {"v80-100": "full", "v60-80": "most", "v40-60": "partial", "v0-40": "none"}

    for value, expect in levels.items():
        level = VisibilityLevel.from_value(value)
        expect_level = VisibilityLevel(expect)
        assert level == expect_level


def test_visibility_json(visibility_json) -> None:
    """Test loading visibility from a json file."""
    schemas = Visibility.from_json(visibility_json)
    serialized = serialize_schemas(schemas)
    assert isinstance(serialized, list)


def test_visibility(visibility_dict) -> None:
    """Test loading visibility from a dictionary."""
    schema = Visibility.from_dict(visibility_dict)
    serialized = serialize_schema(schema)
    assert serialized == visibility_dict


def test_new_visibility(visibility_dict) -> None:
    """Test generating visibility with a new token."""
    without_token = {k: v for k, v in visibility_dict.items() if k != "token"}
    ret = Visibility.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != visibility_dict["token"]
