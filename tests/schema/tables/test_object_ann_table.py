from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np
from pycocotools import mask as cocomask

from t4_devkit.common.serialize import serialize_dataclass, serialize_dataclasses
from t4_devkit.schema import ObjectAnn
from t4_devkit.schema.tables.object_ann import RLEMask

SAMPLE = Path(__file__).parents[2] / "sample" / "t4dataset"


def test_object_ann_json(object_ann_json) -> None:
    """Test loading object ann from a json file."""
    schemas = ObjectAnn.from_json(object_ann_json)
    serialized = serialize_dataclasses(schemas)
    assert isinstance(serialized, list)


def test_object_ann(object_ann_dict) -> None:
    """Test loading object ann from a dictionary."""
    schema = ObjectAnn.from_dict(object_ann_dict)
    serialized = serialize_dataclass(schema)
    assert serialized == object_ann_dict


def test_new_object_ann(object_ann_dict) -> None:
    """Test generating object ann with a new token."""
    without_token = {k: v for k, v in object_ann_dict.items() if k != "token"}
    ret = ObjectAnn.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != object_ann_dict["token"]


def test_rle_mask_size_order() -> None:
    """`size` is (height, width) as COCO writes it: a mask decodes to that shape, and `width` /
    `height` read it in that order."""
    pixels = np.zeros((48, 64), dtype=np.uint8, order="F")
    pixels[10:20, 30:50] = 1
    encoded = cocomask.encode(pixels)
    mask = RLEMask(size=encoded["size"], counts=base64.b64encode(encoded["counts"]).decode())
    assert mask.size == (48, 64) and (mask.height, mask.width) == (48, 64)
    assert mask.decode().shape == (48, 64) and mask.decode().sum() == 200


def test_sample_masks_match_their_images() -> None:
    """The sample dataset's masks decode to their image's (height, width)."""
    with open(SAMPLE / "annotation/sample_data.json") as f:
        frames = {record["token"]: record for record in json.load(f)}
    with open(SAMPLE / "annotation/object_ann.json") as f:
        records = [record for record in json.load(f) if record["mask"].get("counts")]
    assert records
    for record in records:
        frame = frames[record["sample_data_token"]]
        mask = RLEMask(**record["mask"])
        assert mask.decode().shape == (frame["height"], frame["width"])
        assert (mask.width, mask.height) == (frame["width"], frame["height"])
