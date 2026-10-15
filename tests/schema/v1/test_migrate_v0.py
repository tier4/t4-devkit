from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from t4_devkit.common.io import load_pointcloud
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
    np.arange(8, dtype=np.uint8).tofile(labels)
    lidarseg = [
        {
            "token": "seg0",
            "filename": "lidarseg/annotation/frame0.bin",
            "sample_data_token": frames[0]["token"],
        }
    ]
    (annotation / "lidarseg.json").write_text(json.dumps(lidarseg))
    return data_root


def test_migrate_lidar_labels(tmp_path: Path) -> None:
    """Integer fields get 1.0 dtypes, an unrecorded ring is dropped, lidarseg gives label columns."""
    data_root = _semseg_copy(tmp_path)
    with pytest.raises(ValueError, match="unpainted"):
        _migrate_lidar(data_root, tmp_path / "rejected")

    categories = json.loads((data_root / "annotation/category.json").read_text())
    categories = [{"token": "unpainted", "name": "unpainted", "description": ""}, *categories]
    for index, category in enumerate(categories):
        category["index"] = index
    (data_root / "annotation/category.json").write_text(json.dumps(categories))
    migrator = _migrate_lidar(data_root, tmp_path / "sample")

    (lidar,) = migrator.lidars()
    assert [(f.name, f.dtype) for f in lidar.lidar.fields] == [
        ("x", "float32"),
        ("y", "float32"),
        ("z", "float32"),
        ("intensity", "uint8"),
        ("label", "uint8"),
        ("instance", "uint32"),
    ]
    assert "'channel' dropped" in migrator.notes[0]
    path = tmp_path / "sample" / lidar.lidar.container.path
    labeled = load_pointcloud(path, frame_index=0)
    assert labeled["label"].tolist() == list(range(8))
    assert labeled["instance"].tolist() == [0] * 8
    assert "label" not in load_pointcloud(path, frame_index=1)
