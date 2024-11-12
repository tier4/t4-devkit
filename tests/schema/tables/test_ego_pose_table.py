from t4_devkit.schema import EgoPose


def test_ego_pose_json(ego_pose_json) -> None:
    """Test loading ego pose from a json file."""
    _ = EgoPose.from_json(ego_pose_json)


def test_ego_pose(ego_pose_dict) -> None:
    """Test loading ego pose from a dictionary."""
    _ = EgoPose.from_dict(ego_pose_dict)
