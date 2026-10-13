from __future__ import annotations

import base64
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
from pycocotools import mask as cocomask

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
        # box on pixel edges around the decoded mask, which is (height, width)
        rows, cols = np.nonzero(record.mask.decode())
        assert tuple(record.bbox) == (cols.min(), rows.min(), cols.max() + 1, rows.max() + 1)


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


def test_load_v0_vehicle_state() -> None:
    """0.x vehicle states convert; the 0.x forward gear name becomes DRIVE."""
    states = load_dataset(SAMPLE_V0).tables[SchemaName.VEHICLE_STATE]

    assert len(states) == 3
    assert all(state.shift_state == "DRIVE" for state in states)
    assert all(state.source == "vehicle_interface" for state in states)


def test_load_v0_capture_time(tmp_path: Path) -> None:
    """An empty 0.x `data_captured` becomes the first sample time."""
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    log_path = data_root / "annotation" / "log.json"
    logs = json.loads(log_path.read_text())
    logs[0]["data_captured"] = ""
    log_path.write_text(json.dumps(logs))

    tables = load_dataset(data_root).tables
    first = min(sample.timestamp for sample in tables[SchemaName.SAMPLE])
    expected = datetime.fromtimestamp(first / 1e6, tz=timezone.utc).isoformat()
    assert tables[SchemaName.LOG][0].data_captured == expected


@pytest.mark.parametrize(
    ("table", "way_key"),
    [
        ("traffic_light", "primitive_id"),
        ("traffic_light_instance_map", "traffic_light_linestring_id"),
    ],
)
def test_load_v0_traffic_light(tmp_path: Path, table: str, way_key: str) -> None:
    """A 0.x lamp-to-way row sets the instance's lanelet2 way."""
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    instance_token = json.loads((data_root / "annotation" / "instance.json").read_text())[0][
        "token"
    ]
    rows = [{"token": "tl0", "instance_token": instance_token, way_key: "1234"}]
    (data_root / "annotation" / f"{table}.json").write_text(json.dumps(rows))

    tables = load_dataset(data_root).tables
    assert tables[SchemaName.TRAFFIC_LIGHT] == []
    map_element = tables[SchemaName.INSTANCE][0].map_element
    assert (map_element.id, map_element.type) == (1234, "way")


def test_load_v0_source_lidar(tmp_path: Path) -> None:
    """A source LiDAR takes the concatenated channel's fields and counts frames with its points."""
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    annotation = data_root / "annotation"

    def edit(name: str, change) -> None:
        path = annotation / f"{name}.json"
        path.write_text(json.dumps(change(json.loads(path.read_text()))))

    source = {"token": "src", "channel": "LIDAR_SOURCE", "modality": "lidar"}
    calibration = {"token": "src_calib", "sensor_token": "src"}
    calibration |= {"translation": [0.0, 0.0, 0.0], "rotation": [1.0, 0.0, 0.0, 0.0]}
    calibration |= {"camera_intrinsic": [], "camera_distortion": []}
    edit("sensor", lambda records: [*records, source])
    edit("calibrated_sensor", lambda records: [*records, calibration])

    def add_info(records: list[dict]) -> list[dict]:
        frames = [r for r in records if r["filename"].startswith("data/LIDAR_TOP")]
        for i, record in enumerate(frames):
            record["info_filename"] = f"data/LIDAR_TOP_INFO/{i}.json"
            # points from the source in the first two frames only
            sources = [{"sensor_token": "src", "idx_begin": 0, "length": 10 if i < 2 else 0}]
            info = {"num_pts_feats": 7, "sources": sources}
            (data_root / record["info_filename"]).parent.mkdir(exist_ok=True)
            (data_root / record["info_filename"]).write_text(json.dumps(info))
        return records

    edit("sample_data", add_info)

    sensors = {s.channel: s for s in load_dataset(data_root).tables[SchemaName.SENSOR]}
    concat, source_lidar = sensors["LIDAR_TOP"].lidar, sensors["LIDAR_SOURCE"].lidar
    assert concat.source_channels == ["LIDAR_SOURCE"]
    assert source_lidar.fields == concat.fields and len(concat.fields) == 7
    assert source_lidar.container.frame_count == 2


def test_load_v0_empty_mask(tmp_path: Path) -> None:
    """A box-only 0.x label with an empty placeholder mask has no mask in 1.0."""
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    path = data_root / "annotation" / "object_ann.json"
    records = json.loads(path.read_text())
    empty = cocomask.encode(np.zeros((600, 800), dtype=np.uint8, order="F"))
    # as written by some 0.x tools: (width, height)
    records[0]["mask"] = {"size": [800, 600], "counts": base64.b64encode(empty["counts"]).decode()}
    path.write_text(json.dumps(records))

    annotation = load_dataset(data_root).tables[SchemaName.OBJECT_ANN][0]
    assert annotation.mask is None
    assert list(annotation.bbox) == records[0]["bbox"]
