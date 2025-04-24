from __future__ import annotations

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import VehicleState


def test_vehicle_state_json(vehicle_state_json) -> None:
    """Test loading vehicle state from a json file."""
    schemas = VehicleState.from_json(vehicle_state_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_vehicle_state(vehicle_state_dict) -> None:
    """Test loading vehicle state from a dictionary."""
    schema = VehicleState.from_dict(vehicle_state_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == vehicle_state_dict


def test_new_vehicle_state(vehicle_state_dict) -> None:
    """Test generating vehicle state with a new token."""
    without_token = {k: v for k, v in vehicle_state_dict.items() if k != "token"}
    ret = VehicleState.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != vehicle_state_dict["token"]
