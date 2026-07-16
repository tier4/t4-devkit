from __future__ import annotations

from t4_devkit.common import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import TrafficLight


def test_traffic_light_json(traffic_light_json) -> None:
    """Test loading traffic light data from a json file."""
    schemas = TrafficLight.from_json(traffic_light_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_traffic_light(traffic_light_dict) -> None:
    """Test loading traffic light data from a dictionary."""
    schema = TrafficLight.from_dict(traffic_light_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == traffic_light_dict


def test_new_traffic_light(traffic_light_dict) -> None:
    """Test generating a traffic light with a new token."""
    without_token = {k: v for k, v in traffic_light_dict.items() if k != "token"}
    ret = TrafficLight.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != traffic_light_dict["token"]
