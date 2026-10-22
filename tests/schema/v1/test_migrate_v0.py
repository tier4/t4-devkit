from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from t4_devkit.common.io import load_image, load_pointcloud
from t4_devkit.sanity import sanity_check
from t4_devkit.schema.v1 import SchemaName, V0Migrator

SAMPLE_V0 = Path(__file__).parents[2] / "sample" / "t4dataset"


def _migrate_lidar(data_root: Path, output_root: Path) -> V0Migrator:
    migrator = V0Migrator(data_root, output_root)
    for sensor in migrator.lidars():
        migrator.migrate_lidar(sensor)
    return migrator


def _lidar_frames(migrator: V0Migrator) -> list:
    return sorted(
        (f for f in migrator.tables(SchemaName.SAMPLE_DATA) if f.fileformat.value == "parquet"),
        key=lambda frame: frame.frame_index,
    )


def test_migrate_lidar(tmp_path: Path) -> None:
    """Frames go to one Parquet file with the same values; fields that do not fit stay float32."""
    v0_frames = {
        r["token"]: r["filename"]
        for r in json.loads((SAMPLE_V0 / "annotation/sample_data.json").read_text())
    }
    with pytest.warns(UserWarning) as warned:
        migrator = _migrate_lidar(SAMPLE_V0, tmp_path / "sample")
    assert [str(w.message) for w in warned] == migrator.notes
    assert "'intensity' kept as float32, values in [-0.5, 115.0]" in migrator.notes[0]

    (lidar,) = migrator.lidars()
    assert lidar.lidar.container.path == "data/LIDAR_TOP/LIDAR_TOP.parquet"
    assert lidar.lidar.container.frame_count == 3
    # the sample's intensity and ring have fractional values
    assert [(f.name, f.dtype) for f in lidar.lidar.fields][3:] == [
        ("intensity", "float32"),
        ("channel", "float32"),
    ]

    for i, frame in enumerate(_lidar_frames(migrator)):
        assert (frame.filename, frame.frame_index, frame.num_points) == (
            lidar.lidar.container.path,
            i,
            8,
        )
        expected = np.fromfile(SAMPLE_V0 / v0_frames[frame.token], dtype=np.float32).reshape(-1, 5)
        points = load_pointcloud(tmp_path / "sample" / frame.filename, frame_index=i)
        assert np.array_equal(np.stack(list(points.values()), axis=1), expected)


def _semseg_copy(tmp_path: Path) -> Path:
    """The 0.x sample with integer intensity, ring -1 (not recorded) and labels on frame 0."""
    data_root = tmp_path / "v0"
    shutil.copytree(SAMPLE_V0, data_root)
    annotation = data_root / "annotation"
    frames = sorted(
        (
            r
            for r in json.loads((annotation / "sample_data.json").read_text())
            if "LIDAR" in r["filename"]
        ),
        key=lambda r: r["timestamp"],
    )
    for record in frames:
        path = data_root / record["filename"]
        points = np.fromfile(path, dtype=np.float32).reshape(-1, 5)
        points[:, 3] = np.arange(len(points))
        points[:, 4] = -1
        points.tofile(path)

    labels = data_root / "lidarseg/annotation/frame0.bin"
    labels.parent.mkdir(parents=True)
    np.array([0, 1, 2, 3, 4, 0, 1, 2], dtype=np.uint8).tofile(labels)
    lidarseg = [
        {
            "token": "seg0",
            "filename": "lidarseg/annotation/frame0.bin",
            "sample_data_token": frames[0]["token"],
        }
    ]
    (annotation / "lidarseg.json").write_text(json.dumps(lidarseg))
    return data_root


def _add_unpainted(data_root: Path) -> None:
    """Index the categories from 1, with `unpainted` at 0, as lidarseg datasets have them."""
    path = data_root / "annotation/category.json"
    categories = [{"token": "unpainted", "name": "unpainted", "description": ""}]
    categories += json.loads(path.read_text())
    for index, category in enumerate(categories):
        category["index"] = index
    path.write_text(json.dumps(categories))


def test_migrate_lidar_labels(tmp_path: Path) -> None:
    """Integer fields get 1.0 dtypes, an unrecorded ring is dropped, lidarseg gives label columns."""
    data_root = _semseg_copy(tmp_path)
    with pytest.raises(ValueError, match="unpainted"):
        _migrate_lidar(data_root, tmp_path / "rejected")

    _add_unpainted(data_root)
    migrator = _migrate_lidar(data_root, tmp_path / "sample")

    (lidar,) = migrator.lidars()
    assert [(f.name, f.dtype) for f in lidar.lidar.fields] == [
        ("x", "float32"),
        ("y", "float32"),
        ("z", "float32"),
        ("intensity", "uint8"),
        ("label", "uint8"),
        ("instance", "int16"),
    ]
    assert "'channel' dropped" in migrator.notes[0]
    path = tmp_path / "sample" / lidar.lidar.container.path
    labeled = load_pointcloud(path, frame_index=0)
    assert labeled["label"].tolist() == [0, 1, 2, 3, 4, 0, 1, 2]
    assert labeled["instance"].tolist() == [-1] * 8
    assert "label" not in load_pointcloud(path, frame_index=1)


def test_migrate_camera(tmp_path: Path) -> None:
    """A camera channel becomes one video; each frame is its own image, in timestamp order."""
    data_root = tmp_path / "v0"
    shutil.copytree(SAMPLE_V0, data_root)
    migrator = V0Migrator(data_root, tmp_path / "sample")
    sensor = migrator.cameras()[0]
    frames = migrator._channel_frames(sensor)
    sources = []
    for i, frame in enumerate(frames):  # distinct images: gray levels 50, 100, 150
        image = np.full((600, 800, 3), 50 * (i + 1), dtype=np.uint8)
        Image.fromarray(image).save(data_root / frame.filename)
        sources.append(image.astype(int))
    migrator.migrate_camera(sensor)

    video = sensor.camera.video
    assert (video.path, video.frame_count, video.timescale) == (
        "data/CAM_FRONT/CAM_FRONT.mp4",
        3,
        1,
    )
    for i, frame in enumerate(frames):
        assert (frame.filename, frame.frame_index) == (video.path, i)
        image = load_image(tmp_path / "sample" / video.path, frame_index=i).astype(int)
        errors = [np.abs(image - source).mean() for source in sources]
        assert errors[i] < 2 and np.argmin(errors) == i


def test_copy_images(tmp_path: Path) -> None:
    """Kept images are copied with their paths; their records do not change."""
    migrator = V0Migrator(SAMPLE_V0, tmp_path / "sample")
    sensor = migrator.cameras()[0]
    migrator.copy_images(sensor)

    for frame in migrator._channel_frames(sensor):
        assert frame.frame_index is None
        assert (tmp_path / "sample" / frame.filename).read_bytes() == (
            SAMPLE_V0 / frame.filename
        ).read_bytes()


def test_relink_half_linked_frame(tmp_path: Path) -> None:
    """A frame its neighbors skip (as 0.x placeholders can be) is linked back in time order."""
    data_root = tmp_path / "v0"
    shutil.copytree(SAMPLE_V0, data_root)
    path = data_root / "annotation/sample_data.json"
    records = json.loads(path.read_text())
    first, middle, last = sorted(
        (r for r in records if r["filename"].startswith("data/CAM_FRONT/")),
        key=lambda r: r["timestamp"],
    )
    first["next"], last["prev"] = last["token"], first["token"]  # both skip `middle`
    path.write_text(json.dumps(records))

    migrator = V0Migrator(data_root, tmp_path / "sample")
    sensor = migrator.cameras()[0]
    migrator.copy_images(sensor)

    frames = migrator._channel_frames(sensor)
    assert [frame.next for frame in frames] == [middle["token"], last["token"], None]
    assert [frame.prev for frame in frames] == [None, first["token"], middle["token"]]
    assert migrator.notes == ["CAM_FRONT: next / prev relinked in time order on 2 frames"]


def test_migrate_lidarseg_passes_sanity(tmp_path: Path) -> None:
    """A migrated lidarseg dataset passes the 1.0 rules; its instances get indices from 0."""
    data_root = _semseg_copy(tmp_path)
    _add_unpainted(data_root)
    output_root = tmp_path / "sample" / "1"
    V0Migrator(data_root, output_root).migrate("sample", 1)

    instances = json.loads((output_root / "annotation/instance.json").read_text())
    assert [instance["index"] for instance in instances] == [0, 1, 2]
    reports = sanity_check(output_root.parent.as_posix(), revision="1").reports
    assert not [report.id for report in reports if report.is_failed()]


def test_migrate_lidar_sources(tmp_path: Path) -> None:
    """`.info` sources become `source_index` (the source's `sensor.index`) and µs timestamps."""
    data_root = tmp_path / "v0"
    shutil.copytree(SAMPLE_V0, data_root)
    annotation = data_root / "annotation"
    sensors = json.loads((annotation / "sensor.json").read_text())
    top = next(sensor for sensor in sensors if sensor["channel"] == "LIDAR_TOP")
    sensors.append(dict(top, token="rear", channel="LIDAR_REAR"))
    (annotation / "sensor.json").write_text(json.dumps(sensors))
    calibrations = json.loads((annotation / "calibrated_sensor.json").read_text())
    top_calibration = next(c for c in calibrations if c["sensor_token"] == top["token"])
    calibrations.append(dict(top_calibration, token="rear_calibration", sensor_token="rear"))
    (annotation / "calibrated_sensor.json").write_text(json.dumps(calibrations))

    records = json.loads((annotation / "sample_data.json").read_text())
    (data_root / "data/LIDAR_TOP_INFO").mkdir()
    for i, record in enumerate(r for r in records if "LIDAR" in r["filename"]):
        record["info_filename"] = f"data/LIDAR_TOP_INFO/{i}.json"
        info = {
            "sources": [
                {
                    "sensor_token": top["token"],
                    "idx_begin": 0,
                    "length": 5,
                    "stamp": {"sec": 100, "nanosec": 1_000},
                },
                {
                    "sensor_token": "rear",
                    "idx_begin": 5,
                    "length": 3,
                    "stamp": {"sec": 100, "nanosec": 2_000_999},
                },
            ]
        }
        (data_root / record["info_filename"]).write_text(json.dumps(info))
    (annotation / "sample_data.json").write_text(json.dumps(records))

    with pytest.warns(UserWarning):
        migrator = _migrate_lidar(data_root, tmp_path / "sample")
    sensors = {sensor.channel: sensor for sensor in migrator.tables(SchemaName.SENSOR)}
    concat, rear = sensors["LIDAR_TOP"], sensors["LIDAR_REAR"]
    points = load_pointcloud(tmp_path / "sample" / concat.lidar.container.path, frame_index=0)
    assert points["source_index"].tolist() == [concat.index] * 5 + [rear.index] * 3
    assert points["source_timestamp"].tolist() == [100_000_001] * 5 + [100_002_000] * 3
    # the source LiDAR has no file of its own: its points are in the merged one
    assert (rear.lidar.container.format.value, rear.lidar.container.path) == ("parquet", None)
    assert rear.lidar.fields == concat.lidar.fields


def test_migrate_recalibrated_channel(tmp_path: Path) -> None:
    """Two calibrations of one channel would share its file: migration stops instead."""
    data_root = tmp_path / "v0"
    shutil.copytree(SAMPLE_V0, data_root)
    annotation = data_root / "annotation"
    calibrations = json.loads((annotation / "calibrated_sensor.json").read_text())
    calibrations.append(dict(calibrations[0], token="recalibrated"))  # LIDAR_TOP again
    (annotation / "calibrated_sensor.json").write_text(json.dumps(calibrations))
    records = json.loads((annotation / "sample_data.json").read_text())
    last = max((r for r in records if "LIDAR" in r["filename"]), key=lambda r: r["timestamp"])
    last["calibrated_sensor_token"] = "recalibrated"
    (annotation / "sample_data.json").write_text(json.dumps(records))

    with pytest.warns(UserWarning), pytest.raises(FileExistsError, match="LIDAR_TOP"):
        _migrate_lidar(data_root, tmp_path / "sample")
