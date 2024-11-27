from t4_devkit.schema import CalibratedSensor


def test_calibrated_sensor_json(calibrated_sensor_json) -> None:
    """Test loading calibrated sensor from a json file."""
    _ = CalibratedSensor.from_json(calibrated_sensor_json)


def test_calibrated_sensor(calibrated_sensor_dict) -> None:
    """Test loading calibrated sensor from a dictionary."""
    _ = CalibratedSensor.from_dict(calibrated_sensor_dict)


def test_new_calibrated_sensor(calibrated_sensor_dict) -> None:
    """Test generating calibrated sensor with a new token."""
    without_token = {k: v for k, v in calibrated_sensor_dict.items() if k != "token"}
    ret = CalibratedSensor.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != calibrated_sensor_dict["token"]
