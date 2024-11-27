from t4_devkit.schema import Sample


def test_sample_json(sample_json) -> None:
    """Test loading sample from a json file."""
    _ = Sample.from_json(sample_json)


def test_sample(sample_dict) -> None:
    """Test loading sample from a dictionary."""
    _ = Sample.from_dict(sample_dict)


def test_new_sample(sample_dict) -> None:
    """Test generating sample with a new token."""
    without_token = {k: v for k, v in sample_dict.items() if k != "token"}
    ret = Sample.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != sample_dict["token"]
