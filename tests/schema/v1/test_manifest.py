from __future__ import annotations

import json
from pathlib import Path

import pytest

from t4_devkit.common.serialize import serialize_dataclass
from t4_devkit.schema.v1 import Manifest, load_manifest

SAMPLE_ROOT = Path(__file__).parents[2] / "sample"


def test_load_manifest_v1() -> None:
    """A 1.0 dataset has a manifest, and every field round-trips."""
    data_root = SAMPLE_ROOT / "t4dataset_v1"
    manifest = load_manifest(data_root)

    assert isinstance(manifest, Manifest)
    assert manifest.schema_version == "1.0.0"
    assert serialize_dataclass(manifest) == json.loads((data_root / "manifest.json").read_text())


def test_load_manifest_v0() -> None:
    """A 0.x dataset has no manifest."""
    assert load_manifest(SAMPLE_ROOT / "t4dataset") is None


def test_unsupported_schema_version() -> None:
    data = json.loads((SAMPLE_ROOT / "t4dataset_v1" / "manifest.json").read_text())
    data["schema_version"] = "2.0.0"
    with pytest.raises(ValueError, match="Unsupported schema_version"):
        Manifest(**data)


@pytest.mark.parametrize(
    ("key", "value"),
    [("is_synthetic", "yes"), ("version", -1), ("migration_notes", "note")],
)
def test_invalid_field_type(key: str, value: object) -> None:
    data = json.loads((SAMPLE_ROOT / "t4dataset_v1" / "manifest.json").read_text())
    data[key] = value
    with pytest.raises((TypeError, ValueError)):
        Manifest(**data)


def test_invalid_sha256() -> None:
    data = json.loads((SAMPLE_ROOT / "t4dataset_v1" / "manifest.json").read_text())
    data["assets"][0]["sha256"] = "not-a-hash"
    with pytest.raises(ValueError):
        Manifest(**data)
