from t4_devkit.schema import Instance


def test_instance_json(instance_json) -> None:
    """Test loading instance from a json file."""
    _ = Instance.from_json(instance_json)


def test_instance(instance_dict) -> None:
    """Test loading instance from a dictionary."""
    _ = Instance.from_dict(instance_dict)
