from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from t4_devkit.common.serialize import serialize_dataclasses
from t4_devkit.schema.v1 import Camera, Lidar, Sensor

SENSOR_JSON = Path(__file__).parents[2] / "sample" / "t4dataset_v1" / "annotation" / "sensor.json"


@pytest.fixture
def sensor_records() -> list[dict]:
    return json.loads(SENSOR_JSON.read_text())


def test_sensor_json(sensor_records) -> None:
    """The sample's sensors load, and every field round-trips."""
    sensors = Sensor.from_json(SENSOR_JSON)

    assert isinstance(sensors[0].camera, Camera)
    assert isinstance(sensors[1].lidar, Lidar)
    assert serialize_dataclasses(sensors) == sensor_records


def test_block_must_match_modality(sensor_records) -> None:
    camera = copy.deepcopy(sensor_records[0])
    camera["lidar"] = sensor_records[1]["lidar"]
    with pytest.raises(ValueError, match="only the 'camera' block"):
        Sensor.from_dict(camera)


@pytest.mark.parametrize(
    ("block", "key", "value"),
    [
        ("video", "bit_depth", 12),
        ("video", "format", "h264"),
        (None, "intrinsic", []),
        (None, "distortion_model", "rational_polynomial"),
    ],
)
def test_invalid_camera(sensor_records, block, key, value) -> None:
    camera = copy.deepcopy(sensor_records[0])
    target = camera["camera"][block] if block else camera["camera"]
    target[key] = value
    with pytest.raises(ValueError):
        Sensor.from_dict(camera)
