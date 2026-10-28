from __future__ import annotations

import copy
import json

import pytest

from t4_devkit.schema.v1 import SCHEMAS, SchemaName
from tests.helpers import SAMPLE_V1


def _set(path: tuple, value: object):
    """Return an edit that sets `value` at `path` (keys / indices) in the record."""

    def edit(record: dict, records: list[dict]) -> None:
        target = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return edit


def _other_lidar_block(record: dict, records: list[dict]) -> None:
    record["lidar"] = records[1]["lidar"]


# (table, position, edit, error): one invalid value per case; the whole table round-trips in
# test_loader.py::test_load_dataset.
CASES = {
    "empty-string-link": ("sample", 0, _set(("prev",), ""), ValueError),
    "frame-without-file": ("sample_data", 0, _set(("filename",), None), TypeError),
    "frame-without-sample": ("sample_data", -1, _set(("sample_token",), None), TypeError),
    "covariance-length": ("ego_pose", 0, _set(("covariance",), [0.0] * 35), ValueError),
    "imu-length": ("ego_pose", 0, _set(("imu",), [0.0] * 3), ValueError),
    "annotation-type": ("sample_annotation", 0, _set(("annotation_type",), "human"), ValueError),
    "confidence-range": ("sample_annotation", 0, _set(("confidence",), 1.5), ValueError),
    "instance-index-range": ("instance", 0, _set(("index",), 2**15), ValueError),
    "keypoints-shape": ("keypoint", 0, _set(("keypoints",), [1.0, 2.0]), ValueError),
    "scenario-end-before-start": ("scenario", 0, _set(("end_timestamp",), 0), ValueError),
    "traffic-light-color": (
        "traffic_light",
        0,
        _set(("elements", 0, "color"), "yellow"),
        ValueError,
    ),
    "caption-type": ("caption", 0, _set(("caption_type",), "summary"), ValueError),
    "caption-empty-text": ("caption", 0, _set(("text",), ""), ValueError),
    "caption-end-before-start": ("caption", 0, _set(("end_timestamp",), 0), ValueError),
    "sensor-index-range": ("sensor", 0, _set(("index",), 256), ValueError),
    "sensor-index-missing": ("sensor", 0, _set(("index",), None), TypeError),
    "sensor-block-modality": ("sensor", 0, _other_lidar_block, ValueError),
    "video-bit-depth": ("sensor", 0, _set(("camera", "video", "bit_depth"), 12), ValueError),
    "video-format": ("sensor", 0, _set(("camera", "video", "format"), "h264"), ValueError),
    "camera-intrinsic": ("sensor", 0, _set(("camera", "intrinsic"), []), ValueError),
    "distortion-model": (
        "sensor",
        0,
        _set(("camera", "distortion_model"), "rational_polynomial"),
        ValueError,
    ),
}


@pytest.mark.parametrize(("table", "position", "edit", "error"), CASES.values(), ids=CASES.keys())
def test_invalid_record(table: str, position: int, edit, error: type[Exception]) -> None:
    """A record with one invalid value is rejected when built; unedited, it builds."""
    schema = SCHEMAS.get(SchemaName(table))
    records = json.loads((SAMPLE_V1 / "annotation" / f"{table}.json").read_text())
    record = records[position]
    schema.from_dict(copy.deepcopy(record))
    edit(record, records)
    with pytest.raises(error):
        schema.from_dict(record)
