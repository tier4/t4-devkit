from __future__ import annotations

import json
from pathlib import Path

import pytest

from t4_devkit.common.serialize import serialize_dataclasses
from t4_devkit.schema.v1 import Route, Scenario, TrafficLight, Vehicle, VehicleState

ANNOTATION_DIR = Path(__file__).parents[2] / "sample" / "t4dataset_v1" / "annotation"


@pytest.mark.parametrize(
    ("schema", "name"),
    [
        (Vehicle, "vehicle"),
        (VehicleState, "vehicle_state"),
        (Route, "route"),
        (Scenario, "scenario"),
        (TrafficLight, "traffic_light"),
    ],
)
def test_table_json(schema, name: str) -> None:
    """The sample's table loads, and every field round-trips."""
    filepath = ANNOTATION_DIR / f"{name}.json"
    records = schema.from_json(filepath)
    assert serialize_dataclasses(records) == json.loads(filepath.read_text())


def test_scenario_end_before_start() -> None:
    data = json.loads((ANNOTATION_DIR / "scenario.json").read_text())[0]
    data["end_timestamp"] = data["start_timestamp"] - 1
    with pytest.raises(ValueError):
        Scenario.from_dict(data)


def test_invalid_traffic_light_color() -> None:
    data = json.loads((ANNOTATION_DIR / "traffic_light.json").read_text())[0]
    data["elements"][0]["color"] = "yellow"
    with pytest.raises(ValueError):
        TrafficLight.from_dict(data)
