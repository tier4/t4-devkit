from __future__ import annotations

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import Log


def test_log_json(log_json) -> None:
    """Test loading log from a json file."""
    schemas = Log.from_json(log_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_log(log_dict) -> None:
    """Test loading log from a dictionary."""
    schema = Log.from_dict(log_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == log_dict


def test_new_log(log_dict) -> None:
    """Test generating log with a new token."""
    without_token = {k: v for k, v in log_dict.items() if k != "token"}
    ret = Log.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != log_dict["token"]
