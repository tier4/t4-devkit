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
    extra = {**samples[0], "token": "f" * 32}  # sorts after `first`
    _edit_v0(data_root, "sample", lambda records: [*records, extra])
    _edit_v0(
        data_root,
        "sample_data",
        lambda records: [
            {**r, "sample_token": extra["token"]} if r["filename"] == "data/CAM_BACK/001.jpg" else r
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
            {**r, "is_key_frame": False} if r["token"] == labeled["sample_data_token"] else r
            for r in records
        ],
    )
    frame = load_dataset(data_root).get(SchemaName.SAMPLE_DATA, labeled["sample_data_token"])
    assert frame.is_key_frame
