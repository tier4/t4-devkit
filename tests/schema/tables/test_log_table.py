from t4_devkit.schema import Log


def test_log_json(log_json) -> None:
    """Test loading log from a json file."""
    _ = Log.from_json(log_json)


def test_log(log_dict) -> None:
    """Test loading log from a dictionary."""
    _ = Log.from_dict(log_dict)
