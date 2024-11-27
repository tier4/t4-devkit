from t4_devkit.schema import VehicleState


def test_vehicle_state_json(vehicle_state_json) -> None:
    """Test loading vehicle state from a json file."""
    _ = VehicleState.from_json(vehicle_state_json)


def test_vehicle_state(vehicle_state_dict) -> None:
    """Test loading vehicle state from a dictionary."""
    _ = VehicleState.from_dict(vehicle_state_dict)


def test_new_vehicle_state(vehicle_state_dict) -> None:
    """Test generating vehicle state with a new token."""
    without_token = {k: v for k, v in vehicle_state_dict.items() if k != "token"}
    ret = VehicleState.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != vehicle_state_dict["token"]
