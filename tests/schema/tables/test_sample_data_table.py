from __future__ import annotations

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import FileFormat, SampleData


def test_fileformat() -> None:
    """Test FileFormat enum."""

    fileformats = ("jpg", "png", "pcd", "bin", "pcd.bin")

    # check all enum members are covered by above names
    members: list[str] = [m.value for m in FileFormat]
    assert set(members) == set(fileformats)

    # check .values() method
    assert set(FileFormat.values()) == set(fileformats)

    # check each member can construct and its method is valid
    for value in fileformats:
        # check is_member() method
        assert FileFormat.is_member(value)

        member = FileFormat(value)

        # check as_ext() returns .value
        assert member.as_ext() == f".{value}"


def test_sample_data_json(sample_data_json) -> None:
    """Test loading sample data from a json file."""
    schemas = SampleData.from_json(sample_data_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_sample_data(sample_data_dict) -> None:
    """Test loading sample data from a dictionary."""
    schema = SampleData.from_dict(sample_data_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == sample_data_dict


def test_new_sample_data(sample_data_dict) -> None:
    """Test generating sample data with a new token."""
    without_token = {k: v for k, v in sample_data_dict.items() if k != "token"}
    ret = SampleData.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != sample_data_dict["token"]
    assert ret.token != sample_data_dict["token"]
