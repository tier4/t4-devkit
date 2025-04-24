from __future__ import annotations

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import Category


def test_category_json(category_json) -> None:
    """Test loading category from a json file."""
    schemas = Category.from_json(category_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_category(category_dict) -> None:
    """Test loading sample data from a dictionary."""
    schema = Category.from_dict(category_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == category_dict


def test_new_category(category_dict) -> None:
    """Test generating category with a new token."""
    without_token = {k: v for k, v in category_dict.items() if k != "token"}
    ret = Category.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != category_dict["token"]
