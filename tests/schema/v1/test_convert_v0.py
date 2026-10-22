from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
from pycocotools import mask as cocomask

from t4_devkit.schema.v1 import SchemaName, V0Converter, load_dataset
from tests.helpers import SAMPLE_V0, SampleCopy

set_field = SampleCopy.set_field


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

    sample = SampleCopy(tmp_path, SAMPLE_V0)
    sample.edit("category", lambda records: set_field(records, 0, index=5))
    with pytest.raises(ValueError, match="index"):
        load_dataset(sample.root)


def test_load_v0_frames(tmp_path: Path) -> None:
    """Every 0.x frame is a 1.0 sample, grouped by frame number; 0.x key samples keep their token."""
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    sample_data = sample.read("sample_data")
    lidar2 = next(r for r in sample_data if r["filename"] == "data/LIDAR_TOP/002.pcd.bin")
    lidar3 = next(r for r in sample_data if r["filename"] == "data/LIDAR_TOP/003.pcd.bin")

    def sweep(records: list[dict]) -> list[dict]:
        # as the 0.x converter writes a non-key frame: linked to the next sample
        for record in records:
            if record["token"] == lidar2["token"]:
                record.update(is_key_frame=False, sample_token=lidar3["sample_token"])
        return records

    sample.edit("sample_data", sweep)
    dataset = load_dataset(sample.root)
    frame = dataset.get(SchemaName.SAMPLE_DATA, lidar2["token"])
    assert frame.sample_token == lidar2["sample_token"]  # its own frame's sample, not the next
    assert not frame.is_key_frame
    assert dataset.get(SchemaName.SAMPLE, frame.sample_token).has_key_frame  # cameras are key
    samples = dataset.tables[SchemaName.SAMPLE]
    assert len(samples) == 3 and all(len(s.data) == 3 for s in samples)


def test_load_v0_per_camera_samples(tmp_path: Path) -> None:
    """0.x samples of one frame (one per camera image) merge into one 1.0 sample."""
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    first = sample.read("sample")[0]
    extra = dict(first, token="f" * 32)  # sorts after `first`
    sample.edit("sample", lambda records: [*records, extra])
    sample.edit(
        "sample_data",
        lambda records: [
            dict(r, sample_token=extra["token"]) if r["filename"] == "data/CAM_BACK/001.jpg" else r
            for r in records
        ],
    )

    dataset = load_dataset(sample.root)
    assert len(dataset.tables[SchemaName.SAMPLE]) == 3
    channels = set(dataset.get(SchemaName.SAMPLE, first["token"]).data)
    assert channels == {"LIDAR_TOP", "CAM_FRONT", "CAM_BACK"}


def test_load_v0_mask_only_frame_is_key(tmp_path: Path) -> None:
    """A non-key 0.x frame whose only label is a semantic mask (`surface_ann`) is a key frame."""
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    token = sample.read("surface_ann")[0]["sample_data_token"]
    sample.edit(
        "sample_data",
        lambda records: [
            dict(r, is_key_frame=False) if r["token"] == token else r for r in records
        ],
    )
    sample.edit(
        "object_ann", lambda records: [r for r in records if r["sample_data_token"] != token]
    )
    assert load_dataset(sample.root).get(SchemaName.SAMPLE_DATA, token).is_key_frame


def test_load_v0_labeled_frame_is_key(tmp_path: Path) -> None:
    """A 0.x 2D label on a non-key frame makes it a key frame."""
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    labeled = sample.read("object_ann")[0]
    sample.edit(
        "sample_data",
        lambda records: [
            dict(r, is_key_frame=False) if r["token"] == labeled["sample_data_token"] else r
            for r in records
        ],
    )
    frame = load_dataset(sample.root).get(SchemaName.SAMPLE_DATA, labeled["sample_data_token"])
    assert frame.is_key_frame


def test_load_v0_vehicle_state() -> None:
    """0.x vehicle states convert; the 0.x forward gear name becomes DRIVE."""
    states = load_dataset(SAMPLE_V0).tables[SchemaName.VEHICLE_STATE]

    assert len(states) == 3
    assert all(state.shift_state == "DRIVE" for state in states)
    assert all(state.source == "vehicle_interface" for state in states)


def test_load_v0_capture_time(tmp_path: Path) -> None:
    """An empty 0.x `data_captured` becomes the first sample time."""
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    sample.edit("log", lambda records: set_field(records, 0, data_captured=""))

    tables = load_dataset(sample.root).tables
    first = min(s.timestamp for s in tables[SchemaName.SAMPLE])
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
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    instance_token = sample.read("instance")[0]["token"]
    row = {"token": "tl0", "instance_token": instance_token, way_key: "1234"}
    (sample.root / "annotation" / f"{table}.json").write_text(json.dumps([row]))

    tables = load_dataset(sample.root).tables
    assert tables[SchemaName.TRAFFIC_LIGHT] == []
    map_element = tables[SchemaName.INSTANCE][0].map_element
    assert (map_element.id, map_element.type) == (1234, "way")


def test_load_v0_source_lidar(tmp_path: Path) -> None:
    """A source LiDAR takes the concatenated channel's fields and counts frames with its points."""
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    source = {"token": "src", "channel": "LIDAR_SOURCE", "modality": "lidar"}
    calibration = {"token": "src_calib", "sensor_token": "src"}
    calibration |= {"translation": [0.0, 0.0, 0.0], "rotation": [1.0, 0.0, 0.0, 0.0]}
    calibration |= {"camera_intrinsic": [], "camera_distortion": []}
    sample.edit("sensor", lambda records: [*records, source])
    sample.edit("calibrated_sensor", lambda records: [*records, calibration])

    def add_info(records: list[dict]) -> list[dict]:
        frames = [r for r in records if r["filename"].startswith("data/LIDAR_TOP")]
        for i, record in enumerate(frames):
            record["info_filename"] = f"data/LIDAR_TOP_INFO/{i}.json"
            # points from the source in the first two frames only
            sources = [{"sensor_token": "src", "idx_begin": 0, "length": 10 if i < 2 else 0}]
            info = {"num_pts_feats": 7, "sources": sources}
            (sample.root / record["info_filename"]).parent.mkdir(exist_ok=True)
            (sample.root / record["info_filename"]).write_text(json.dumps(info))
        return records

    sample.edit("sample_data", add_info)

    sensors = {s.channel: s for s in load_dataset(sample.root).tables[SchemaName.SENSOR]}
    concat, source_lidar = sensors["LIDAR_TOP"].lidar, sensors["LIDAR_SOURCE"].lidar
    assert concat.source_channels == ["LIDAR_SOURCE"]
    assert source_lidar.fields == concat.fields and len(concat.fields) == 7
    assert source_lidar.container.frame_count == 2


def test_load_v0_empty_mask(tmp_path: Path) -> None:
    """A box-only 0.x label with an empty placeholder mask has no mask in 1.0."""
    sample = SampleCopy(tmp_path, SAMPLE_V0)
    empty = cocomask.encode(np.zeros((600, 800), dtype=np.uint8, order="F"))
    # as written by some 0.x tools: (width, height)
    mask = {"size": [800, 600], "counts": base64.b64encode(empty["counts"]).decode()}
    sample.edit("object_ann", lambda records: set_field(records, 0, mask=mask))

    annotation = load_dataset(sample.root).tables[SchemaName.OBJECT_ANN][0]
    assert annotation.mask is None
    assert list(annotation.bbox) == sample.read("object_ann")[0]["bbox"]
