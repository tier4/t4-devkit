from __future__ import annotations

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import LidarSeg


def test_lidarseg_json(lidarseg_json) -> None:
    """Test loading lidarseg from a json file."""
    schemas = LidarSeg.from_json(lidarseg_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_lidarseg(lidarseg_dict) -> None:
    """Test loading lidarseg from a dictionary."""
    schema = LidarSeg.from_dict(lidarseg_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == lidarseg_dict


def test_new_lidarseg(lidarseg_dict) -> None:
    """Test generating lidarseg with a new token."""
    without_token = {k: v for k, v in lidarseg_dict.items() if k != "token"}
    ret = LidarSeg.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != lidarseg_dict["token"]
