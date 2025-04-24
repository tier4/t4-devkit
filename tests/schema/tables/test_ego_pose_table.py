from __future__ import annotations

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import EgoPose


def test_ego_pose_json(ego_pose_json) -> None:
    """Test loading ego pose from a json file."""
    schemas = EgoPose.from_json(ego_pose_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_ego_pose(ego_pose_dict) -> None:
    """Test loading ego pose from a dictionary."""
    schema = EgoPose.from_dict(ego_pose_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == ego_pose_dict


def test_new_ego_pose(ego_pose_dict) -> None:
    """Test generating ego pose with a new token."""
    without_token = {k: v for k, v in ego_pose_dict.items() if k != "token"}
    ret = EgoPose.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != ego_pose_dict["token"]
