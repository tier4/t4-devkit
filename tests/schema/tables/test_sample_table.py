from t4_devkit.schema import Sample


def test_sample_json(sample_json) -> None:
    """Test loading sample from a json file."""
    _ = Sample.from_json(sample_json)


def test_sample(sample_dict) -> None:
    """Test loading sample from a dictionary."""
    _ = Sample.from_dict(sample_dict)
