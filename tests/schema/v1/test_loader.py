from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from t4_devkit.schema.v1 import SCHEMAS, SchemaName, Sensor, load_dataset

SAMPLE_ROOT = Path(__file__).parents[2] / "sample"
SAMPLE_V1 = SAMPLE_ROOT / "t4dataset_v1"


def _copy_without_table(tmp_path: Path, name: str) -> Path:
    data_root = tmp_path / "dataset"
    shutil.copytree(SAMPLE_V1, data_root)
    manifest = json.loads((data_root / "manifest.json").read_text())
    del manifest["tables"][name]
    (data_root / "manifest.json").write_text(json.dumps(manifest))
    return data_root


def test_load_dataset() -> None:
    """Every table is loaded with its 1.0 class, and lookups by token work."""
    dataset = load_dataset(SAMPLE_V1)

    assert dataset.manifest.schema_version == "1.0.0"
    for name in SchemaName:
        records = json.loads((SAMPLE_V1 / "annotation" / name.filename).read_text())
        assert len(dataset.tables[name]) == len(records)
        assert all(isinstance(r, SCHEMAS.get(name)) for r in dataset.tables[name])

    assert isinstance(dataset.get("sensor", "sensor_cam"), Sensor)


def test_shortcuts() -> None:
    """Shortcut fields are filled from the links."""
    dataset = load_dataset(SAMPLE_V1)

    sample = dataset.tables[SchemaName.SAMPLE][0]
    assert set(sample.data) == {"CAM_FRONT", "LIDAR_TOP"}
    assert sample.ann_3ds
    assert sample.ann_2ds

    sample_data = dataset.get("sample_data", sample.data["LIDAR_TOP"])
    assert sample_data.channel == "LIDAR_TOP"
    assert dataset.get("sensor", sample_data.sensor_token).first_sd_token is not None

    assert dataset.tables[SchemaName.SAMPLE_ANNOTATION][0].category_name == "car"
    assert {r.category_name for r in dataset.tables[SchemaName.OBJECT_ANN]} == {"car", "road"}


def test_missing_required_table(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="vehicle"):
        load_dataset(_copy_without_table(tmp_path, "vehicle"))


def test_missing_optional_table(tmp_path: Path) -> None:
    dataset = load_dataset(_copy_without_table(tmp_path, "caption"))
    assert dataset.tables[SchemaName.CAPTION] == []
