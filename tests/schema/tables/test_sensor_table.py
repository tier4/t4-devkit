from t4_devkit.schema import Sensor, SensorModality


def test_sensor_modality() -> None:
    """Test SensorModality enum."""

    modalities = ("lidar", "camera", "radar")

    # check all enum members are covered by above names
    members: list[str] = [m.value for m in SensorModality]
    assert set(members) == set(modalities)

    # check each member can construct
    for value in modalities:
        _ = SensorModality(value)


def test_sensor_json(sensor_json) -> None:
    """Test loading sensor from a json file."""
    _ = Sensor.from_json(sensor_json)


def test_sensor(sensor_dict) -> None:
    """Test loading sensor from a dictionary."""
    _ = Sensor.from_dict(sensor_dict)
