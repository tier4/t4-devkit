from __future__ import annotations

import json
from pathlib import Path

import pytest

from t4_devkit.common.serialize import serialize_dataclasses
from t4_devkit.schema.v1 import Caption

CAPTION_JSON = Path(__file__).parents[2] / "sample" / "t4dataset_v1" / "annotation" / "caption.json"


def test_caption_json() -> None:
    """The sample's captions load, and every field round-trips."""
    records = Caption.from_json(CAPTION_JSON)
    assert serialize_dataclasses(records) == json.loads(CAPTION_JSON.read_text())


@pytest.mark.parametrize(
    ("key", "value"),
    [("caption_type", "summary"), ("text", ""), ("end_timestamp", 0)],
)
def test_invalid_caption(key: str, value: object) -> None:
    data = json.loads(CAPTION_JSON.read_text())[0]
    data[key] = value
    with pytest.raises(ValueError):
        Caption.from_dict(data)
