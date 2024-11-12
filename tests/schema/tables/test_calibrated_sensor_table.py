from t4_devkit.schema import CalibratedSensor


def test_calibrated_sensor_json(calibrated_sensor_json) -> None:
    """Test loading calibrated sensor from a json file."""
    _ = CalibratedSensor.from_json(calibrated_sensor_json)


def test_calibrated_sensor(calibrated_sensor_dict) -> None:
    """Test loading calibrated sensor from a dictionary."""
    _ = CalibratedSensor.from_dict(calibrated_sensor_dict)
