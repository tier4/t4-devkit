from __future__ import annotations

import json
from pathlib import Path

import pytest

from t4_devkit.common.serialize import serialize_dataclasses
from t4_devkit.schema.v1 import EgoPose, Log, Map, Sample, SampleData, Scene

ANNOTATION_DIR = Path(__file__).parents[2] / "sample" / "t4dataset_v1" / "annotation"


@pytest.mark.parametrize(
    ("schema", "name"),
    [
        (Sample, "sample"),
        (SampleData, "sample_data"),
        (EgoPose, "ego_pose"),
        (Scene, "scene"),
        (Log, "log"),
        (Map, "map"),
    ],
)
def test_table_json(schema, name: str) -> None:
    """The sample's table loads, and every field round-trips."""
    filepath = ANNOTATION_DIR / f"{name}.json"
    records = schema.from_json(filepath)
    assert serialize_dataclasses(records) == json.loads(filepath.read_text())


def test_empty_string_link_is_rejected() -> None:
    """Missing links are null in 1.0, never an empty string."""
    data = json.loads((ANNOTATION_DIR / "sample.json").read_text())[0]
    data["prev"] = ""
    with pytest.raises(ValueError):
        Sample.from_dict(data)


def test_invalid_covariance_length() -> None:
    data = json.loads((ANNOTATION_DIR / "ego_pose.json").read_text())[0]
    data["covariance"] = [0.0] * 35
    with pytest.raises(ValueError):
        EgoPose.from_dict(data)
