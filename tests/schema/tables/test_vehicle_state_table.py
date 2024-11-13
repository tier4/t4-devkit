from t4_devkit.schema import VehicleState


def test_vehicle_state_json(vehicle_state_json) -> None:
    """Test loading vehicle state from a json file."""
    _ = VehicleState.from_json(vehicle_state_json)


def test_vehicle_state(vehicle_state_dict) -> None:
    """Test loading vehicle state from a dictionary."""
    s = VehicleState.from_dict(vehicle_state_dict)
    print(s)
