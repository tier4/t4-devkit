from __future__ import annotations

import json
from pathlib import Path

import pytest

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema.v1 import SCHEMAS, SchemaName, Sensor, load_dataset
from tests.helpers import SAMPLE_V1, SampleCopy


def _copy_without_table(tmp_path: Path, name: str) -> Path:
    sample = SampleCopy(tmp_path)
    sample.edit(
        "manifest", lambda m: dict(m, tables={k: v for k, v in m["tables"].items() if k != name})
    )
    return sample.root


def test_load_dataset() -> None:
    """Every table loads with its 1.0 class and every field round-trips, the manifest too;
    lookups by token work."""
    dataset = load_dataset(SAMPLE_V1)

    manifest = json.loads((SAMPLE_V1 / "manifest.json").read_text())
    assert serialize_dataclass(dataset.manifest) == manifest
    for name in SchemaName:
        records = json.loads((SAMPLE_V1 / "annotation" / name.filename).read_text())
        assert all(isinstance(r, SCHEMAS.get(name)) for r in dataset.tables[name])
        assert serialize_dataclasses(dataset.tables[name]) == records, name

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

    # a non-key frame is a sample too, with the channels it has
    non_key = next(s for s in dataset.tables[SchemaName.SAMPLE] if not s.has_key_frame)
    assert set(non_key.data) == {"LIDAR_TOP"}
    assert not non_key.ann_3ds and not non_key.ann_2ds

    assert dataset.tables[SchemaName.SAMPLE_ANNOTATION][0].category_name == "car"
    assert {r.category_name for r in dataset.tables[SchemaName.OBJECT_ANN]} == {"car", "road"}


def test_missing_required_table(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="vehicle"):
        load_dataset(_copy_without_table(tmp_path, "vehicle"))


def test_missing_optional_table(tmp_path: Path) -> None:
    dataset = load_dataset(_copy_without_table(tmp_path, "caption"))
    assert dataset.tables[SchemaName.CAPTION] == []
