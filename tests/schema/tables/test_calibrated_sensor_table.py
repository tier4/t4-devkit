from __future__ import annotations

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import CalibratedSensor


def test_calibrated_sensor_json(calibrated_sensor_json) -> None:
    """Test loading calibrated sensor from a json file."""
    schemas = CalibratedSensor.from_json(calibrated_sensor_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_calibrated_sensor(calibrated_sensor_dict) -> None:
    """Test loading calibrated sensor from a dictionary."""
    schema = CalibratedSensor.from_dict(calibrated_sensor_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == calibrated_sensor_dict


def test_new_calibrated_sensor(calibrated_sensor_dict) -> None:
    """Test generating calibrated sensor with a new token."""
    without_token = {k: v for k, v in calibrated_sensor_dict.items() if k != "token"}
    ret = CalibratedSensor.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != calibrated_sensor_dict["token"]
    assert ret.token != calibrated_sensor_dict["token"]
