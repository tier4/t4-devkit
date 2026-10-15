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
    # 1.0 counts 3D boxes and 2D labels (0.x tools count them differently)
    for instance in tables[SchemaName.INSTANCE]:
        labels = [
            r
            for table in (SchemaName.SAMPLE_ANNOTATION, SchemaName.OBJECT_ANN)
            for r in tables[table]
            if r.instance_token == instance.token
        ]
        assert instance.nbr_annotations == len(labels)

    surfaces = [r for r in tables[SchemaName.OBJECT_ANN] if r.instance_token is None]
    assert len(surfaces) == 2
    for record in surfaces:
        category = dataset.get(SchemaName.CATEGORY, record.category_token)
        assert not category.is_thing
        # box on pixel edges around the decoded mask, which is (height, width)
        rows, cols = np.nonzero(record.mask.decode())
        assert tuple(record.bbox) == (cols.min(), rows.min(), cols.max() + 1, rows.max() + 1)


def test_load_v0_category_index(tmp_path: Path) -> None:
    """Categories without index get their list position; a partly set index is rejected."""
    categories = load_dataset(SAMPLE_V0).tables[SchemaName.CATEGORY]
    assert [category.index for category in categories] == list(range(len(categories)))

    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    category_path = data_root / "annotation" / "category.json"
    records = json.loads(category_path.read_text())
    records[0]["index"] = 5
    category_path.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="index"):
        load_dataset(data_root)


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


def _copy_v0(tmp_path: Path) -> Path:
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V0, data_root)
    return data_root


def _edit_v0(data_root: Path, name: str, change) -> None:
    path = data_root / "annotation" / f"{name}.json"
    path.write_text(json.dumps(change(json.loads(path.read_text()))))


def test_load_v0_frames(tmp_path: Path) -> None:
    """Every 0.x frame is a 1.0 sample, grouped by frame number; 0.x key samples keep their token."""
    data_root = _copy_v0(tmp_path)
    sample_data = json.loads((data_root / "annotation" / "sample_data.json").read_text())
    lidar2 = next(r for r in sample_data if r["filename"] == "data/LIDAR_TOP/002.pcd.bin")
    lidar3 = next(r for r in sample_data if r["filename"] == "data/LIDAR_TOP/003.pcd.bin")

    def sweep(records: list[dict]) -> list[dict]:
        # as the 0.x converter writes a non-key frame: linked to the next sample
        for record in records:
            if record["token"] == lidar2["token"]:
                record.update(is_key_frame=False, sample_token=lidar3["sample_token"])
        return records

    _edit_v0(data_root, "sample_data", sweep)
    dataset = load_dataset(data_root)
    frame = dataset.get(SchemaName.SAMPLE_DATA, lidar2["token"])
    assert frame.sample_token == lidar2["sample_token"]  # its own frame's sample, not the next
    assert not frame.is_key_frame
    assert dataset.get(SchemaName.SAMPLE, frame.sample_token).has_key_frame  # cameras are key
    samples = dataset.tables[SchemaName.SAMPLE]
    assert len(samples) == 3 and all(len(sample.data) == 3 for sample in samples)


def test_load_v0_per_camera_samples(tmp_path: Path) -> None:
    """0.x samples of one frame (one per camera image) merge into one 1.0 sample."""
    data_root = _copy_v0(tmp_path)
    samples = json.loads((data_root / "annotation" / "sample.json").read_text())
    first = samples[0]["token"]
    extra = dict(samples[0], token="f" * 32)  # sorts after `first`
    _edit_v0(data_root, "sample", lambda records: [*records, extra])
    _edit_v0(
        data_root,
        "sample_data",
        lambda records: [
            dict(r, sample_token=extra["token"]) if r["filename"] == "data/CAM_BACK/001.jpg" else r
            for r in records
        ],
    )

    dataset = load_dataset(data_root)
    assert len(dataset.tables[SchemaName.SAMPLE]) == 3
    assert set(dataset.get(SchemaName.SAMPLE, first).data) == {"LIDAR_TOP", "CAM_FRONT", "CAM_BACK"}


def test_load_v0_labeled_frame_is_key(tmp_path: Path) -> None:
    """A 0.x 2D label on a non-key frame makes it a key frame."""
    data_root = _copy_v0(tmp_path)
    labeled = json.loads((data_root / "annotation" / "object_ann.json").read_text())[0]
    _edit_v0(
        data_root,
        "sample_data",
        lambda records: [
            dict(r, is_key_frame=False) if r["token"] == labeled["sample_data_token"] else r
            for r in records
        ],
    )
    frame = load_dataset(data_root).get(SchemaName.SAMPLE_DATA, labeled["sample_data_token"])
    assert frame.is_key_frame


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
