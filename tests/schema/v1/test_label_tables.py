from __future__ import annotations

import json
from pathlib import Path

import pytest

from t4_devkit.common.serialize import serialize_dataclasses
from t4_devkit.schema.v1 import (
    Attribute,
    Category,
    Instance,
    Keypoint,
    ObjectAnn,
    SampleAnnotation,
    Visibility,
)

ANNOTATION_DIR = Path(__file__).parents[2] / "sample" / "t4dataset_v1" / "annotation"


@pytest.mark.parametrize(
    ("schema", "name"),
    [
        (Category, "category"),
        (Attribute, "attribute"),
        (Visibility, "visibility"),
        (Instance, "instance"),
        (SampleAnnotation, "sample_annotation"),
        (ObjectAnn, "object_ann"),
        (Keypoint, "keypoint"),
    ],
)
def test_table_json(schema, name: str) -> None:
    """The sample's table loads, and every field round-trips."""
    filepath = ANNOTATION_DIR / f"{name}.json"
    records = schema.from_json(filepath)
    assert serialize_dataclasses(records) == json.loads(filepath.read_text())


@pytest.mark.parametrize(
    ("key", "value"),
    [("annotation_type", "human"), ("confidence", 1.5)],
)
def test_invalid_label_provenance(key: str, value: object) -> None:
    data = json.loads((ANNOTATION_DIR / "sample_annotation.json").read_text())[0]
    data[key] = value
    with pytest.raises(ValueError):
        SampleAnnotation.from_dict(data)


def test_invalid_keypoints_shape() -> None:
    data = json.loads((ANNOTATION_DIR / "keypoint.json").read_text())[0]
    data["keypoints"] = [1.0, 2.0]
    with pytest.raises(ValueError):
        Keypoint.from_dict(data)
