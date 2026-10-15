from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from t4_devkit.common.io import load_image, load_pointcloud
from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.sanity import sanity_check
from t4_devkit.schema.v1 import DatasetWriter, SchemaName, load_dataset

SAMPLE_V1 = Path(__file__).parents[2] / "sample" / "t4dataset_v1"


def _manifest_info(dataset) -> dict:
    """The manifest fields the caller gives: everything but the files and computed parts."""
    info = serialize_dataclass(dataset.manifest)
    for name in ("tables", "assets", "capabilities"):
        del info[name]
    return info


def _sensor(dataset, channel: str):
    return next(sensor for sensor in dataset.tables[SchemaName.SENSOR] if sensor.channel == channel)


def test_round_trip(tmp_path: Path) -> None:
    """A dataset written from loaded records loads back to the same records, and passes sanity."""
    dataset = load_dataset(SAMPLE_V1)
    data_root = tmp_path / "sample"  # named as the sample's `dataset_id`
    writer = DatasetWriter(data_root)
    for directory in ("data", "map"):
        writer.copy(SAMPLE_V1 / directory, directory)
    manifest = writer.save(dataset.tables, _manifest_info(dataset))

    assert manifest.capabilities == dataset.manifest.capabilities
    assert any(generator.name == "t4-devkit" for generator in manifest.generators)
    loaded = load_dataset(data_root)
    for table in SchemaName:
        assert serialize_dataclasses(loaded.tables[table]) == serialize_dataclasses(
            dataset.tables[table]
        ), table

    result = sanity_check(data_root.as_posix(), checksum=True)
    assert not [report.id for report in result.reports if report.is_failed()]
    assert {report.id for report in result.reports if not report.is_passed(strict=True)} == {
        "STR001",  # no version directory
        "STR005",  # no input_bag
        "STR009",  # no pointcloud map
    }


def test_write_data(tmp_path: Path) -> None:
    """LiDAR and camera frames written by the writer match the sample's sensor rows."""
    dataset = load_dataset(SAMPLE_V1)
    writer = DatasetWriter(tmp_path / "sample")

    lidar = _sensor(dataset, "LIDAR_TOP")
    fields = [(field.name, field.dtype) for field in lidar.lidar.fields]
    frames = [
        load_pointcloud(SAMPLE_V1 / lidar.lidar.container.path, frame_index=i)
        for i in range(lidar.lidar.container.frame_count)
    ]
    path, frame_count = writer.write_lidar("LIDAR_TOP", frames, fields)
    assert (path, frame_count) == (lidar.lidar.container.path, lidar.lidar.container.frame_count)
    for i, frame in enumerate(frames):
        written = load_pointcloud(tmp_path / "sample" / path, frame_index=i)
        assert all((written[name] == frame[name]).all() for name, _ in fields)

    camera = _sensor(dataset, "CAM_FRONT")
    images = (
        load_image(SAMPLE_V1 / camera.camera.video.path, frame_index=i)
        for i in range(camera.camera.video.frame_count)
    )
    video = writer.write_camera("CAM_FRONT", images, frame_rate=camera.camera.video.timescale)
    assert video == serialize_dataclass(camera.camera.video)


def test_existing_folder(tmp_path: Path) -> None:
    with pytest.raises(FileExistsError):
        DatasetWriter(tmp_path)


def test_channel_written_once(tmp_path: Path) -> None:
    """A channel has one file: writing it again is refused, not overwritten."""
    writer = DatasetWriter(tmp_path / "sample")
    fields = [("x", "float32")]
    writer.write_lidar("LIDAR_TOP", [{"x": np.zeros(2, dtype=np.float32)}], fields)
    with pytest.raises(FileExistsError, match="LIDAR_TOP"):
        writer.write_lidar("LIDAR_TOP", [{"x": np.ones(2, dtype=np.float32)}], fields)
