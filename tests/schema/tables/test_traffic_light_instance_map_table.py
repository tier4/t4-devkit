from __future__ import annotations

import pytest

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import TrafficLightInstanceMap


def test_traffic_light_instance_map_json(traffic_light_instance_map_json) -> None:
    """Test loading traffic-light instance-map relation from a json file."""
    schemas = TrafficLightInstanceMap.from_json(traffic_light_instance_map_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_traffic_light_instance_map(traffic_light_instance_map_dict) -> None:
    """Test loading traffic-light instance-map relation from a dictionary."""
    schema = TrafficLightInstanceMap.from_dict(traffic_light_instance_map_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == traffic_light_instance_map_dict


def test_new_traffic_light_instance_map(traffic_light_instance_map_dict) -> None:
    """Test generating traffic-light instance-map relation with a new token."""
    without_token = {k: v for k, v in traffic_light_instance_map_dict.items() if k != "token"}
    ret = TrafficLightInstanceMap.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != traffic_light_instance_map_dict["token"]


@pytest.mark.parametrize(
    "field_to_empty",
    ["instance_token", "traffic_light_linestring_id"],
)
def test_traffic_light_instance_map_rejects_empty_fields(
    traffic_light_instance_map_dict, field_to_empty: str
) -> None:
    """`instance_token`/`traffic_light_linestring_id` must not be empty."""
    invalid = dict(traffic_light_instance_map_dict)
    invalid[field_to_empty] = ""
    with pytest.raises(ValueError):
        TrafficLightInstanceMap.from_dict(invalid)
