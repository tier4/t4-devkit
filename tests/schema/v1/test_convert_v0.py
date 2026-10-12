from __future__ import annotations

import json
import shutil
from pathlib import Path

from t4_devkit.schema.v1 import SchemaName, V0Converter, load_dataset

SAMPLE_V0 = Path(__file__).parents[2] / "sample" / "t4dataset"


def test_load_v0_dataset() -> None:
    """A 0.x dataset loads as 1.0 records, with placeholders for what 0.x never stored."""
    dataset = load_dataset(SAMPLE_V0)
    tables = dataset.tables

    assert dataset.manifest is None
    assert len(tables[SchemaName.SAMPLE]) == 3
    assert len(tables[SchemaName.SAMPLE_DATA]) == 9

    # calibrated_sensor rows become sensor rows with the same tokens
    sensors = {sensor.channel: sensor for sensor in tables[SchemaName.SENSOR]}
    assert sorted(sensor.index for sensor in sensors.values()) == [0, 1, 2]
    camera = sensors["CAM_FRONT"].camera
    assert (camera.width, camera.height) == (800, 600)
    assert camera.distortion_model == "plumb_bob"
    lidar = sensors["LIDAR_TOP"].lidar
    assert lidar.container.format == "bin"
    assert lidar.container.frame_count == 3
    assert [field.name for field in lidar.fields] == ["x", "y", "z", "intensity", "channel"]
    for record in tables[SchemaName.SAMPLE_DATA]:
        assert dataset.get(SchemaName.SENSOR, record.sensor_token).channel in sensors
        assert record.frame_index is None

    # log -> vehicle (placeholders) and map (hash from the file)
    log = tables[SchemaName.LOG][0]
    vehicle = dataset.get(SchemaName.VEHICLE, log.vehicle_token)
    assert vehicle.name == "test_vehicle"
    assert vehicle.model == V0Converter.FALLBACKS["vehicle"]["model"]
    map_ = dataset.get(SchemaName.MAP, log.map_token)
    assert map_.map_id == V0Converter.FALLBACKS["map"]["map_id"]
    assert len(map_.sha256) == 64


def test_load_v0_labels() -> None:
    """Labels convert; surface_ann becomes object_ann without instance, boxed by its mask."""
    dataset = load_dataset(SAMPLE_V0)
    tables = dataset.tables

    assert len(tables[SchemaName.SAMPLE_ANNOTATION]) == 4
    assert all(r.annotation_type == "manual" for r in tables[SchemaName.SAMPLE_ANNOTATION])
    assert tables[SchemaName.INSTANCE][0].name == "car_001"

    surfaces = [r for r in tables[SchemaName.OBJECT_ANN] if r.instance_token is None]
    assert len(surfaces) == 2
    for record in surfaces:
        category = dataset.get(SchemaName.CATEGORY, record.category_token)
        assert not category.is_thing
        xmin, ymin, xmax, ymax = record.bbox
        assert 0 <= xmin < xmax <= record.mask.size[1] and 0 <= ymin < ymax <= record.mask.size[0]


def test_load_v0_autolabel(tmp_path: Path) -> None:
    """A 0.x autolabel becomes annotation_type auto, with the model as provenance."""
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    path = data_root / "annotation" / "sample_annotation.json"
    records = json.loads(path.read_text())
    records[0]["automatic_annotation"] = True
    records[0]["autolabel_metadata"] = [{"name": "centerpoint-v2", "score": 0.8}]
    path.write_text(json.dumps(records))

    annotation = load_dataset(data_root).tables[SchemaName.SAMPLE_ANNOTATION][0]
    assert annotation.annotation_type == "auto"
    assert annotation.provenance == "centerpoint-v2"
    assert annotation.confidence == 0.8


def test_load_v0_visibility(tmp_path: Path) -> None:
    """0.x level aliases are mapped; `unavailable` is dropped and becomes a null visibility_token."""
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    path = data_root / "annotation" / "visibility.json"
    records = json.loads(path.read_text())
    records[0]["level"] = "v80-100"
    records[1]["level"] = "unavailable"
    path.write_text(json.dumps(records))
    path = data_root / "annotation" / "sample_annotation.json"
    annotations = json.loads(path.read_text())
    annotations[0]["visibility_token"] = records[1]["token"]
    path.write_text(json.dumps(annotations))

    tables = load_dataset(data_root).tables
    assert [r.level for r in tables[SchemaName.VISIBILITY]] == ["full", "partial", "none"]
    assert tables[SchemaName.SAMPLE_ANNOTATION][0].visibility_token is None
