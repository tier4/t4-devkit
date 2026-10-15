from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import SampleCopy

set_field = SampleCopy.set_field


def _lidar(records: list[dict], **fields) -> list[dict]:
    """Edit the `lidar` block of the LiDAR sensor."""
    records[1]["lidar"].update(fields)
    return records


MISSING = "0" * 32

# (rule, table, change): each change breaks what the rule checks.
CASES = [
    ("REF015", "sample_data", lambda r: set_field(r, 0, sensor_token=MISSING)),
    ("REF016", "log", lambda r: set_field(r, 0, vehicle_token=MISSING)),
    ("REF017", "log", lambda r: set_field(r, 0, map_token=None)),
    ("REF018", "sample_annotation", lambda r: set_field(r, 0, visibility_token=MISSING)),
    ("REF019", "object_ann", lambda r: set_field(r, 0, category_token=MISSING)),
    ("REF020", "keypoint", lambda r: set_field(r, 0, category_tokens=[MISSING])),
    ("REF021", "traffic_light", lambda r: set_field(r, 0, object_ann_token=MISSING)),
    ("REF022", "route", lambda r: set_field(r, 0, map_token=MISSING)),
    ("REF023", "scenario", lambda r: set_field(r, 0, log_token=MISSING)),
    ("REF024", "caption", lambda r: set_field(r, 0, scenario_token=MISSING)),
    ("REF025", "sensor", lambda r: _lidar(r, source_channels=["CAM_FRONT"])),
    ("REF107", "sample", lambda r: set_field(r, 0, next=r[2]["token"])),
    ("REF108", "sample_data", lambda r: set_field(r, 0, next=r[3]["token"])),
    ("REF204", "sample_data", lambda r: set_field(r, 0, filename="data/CAM_FRONT/other.mp4")),
    ("REF205", "sensor", lambda r: (r[1]["lidar"]["fields"][3].update(dtype="float64"), r)[1]),
    (
        "REF206",
        "sample_data",
        lambda r: [dict(x, num_points=99) if x["num_points"] else x for x in r],
    ),
    ("REF207", "map", lambda r: set_field(r, 0, sha256="0" * 64)),
    ("REF302", "instance", lambda r: set_field(r, 0, map_element={"id": 99999, "type": "way"})),
    ("REF303", "traffic_light", lambda r: set_field(r, 0, regulatory_element_id=99999)),
    (
        "REF304",
        "route",
        lambda r: set_field(
            r, 0, segments=[{"preferred_primitive_id": 99999, "primitive_ids": [99999]}]
        ),
    ),
    ("REF305", "sensor", lambda r: _lidar(r, source_channels=["LIDAR_TOP"])),
]


@pytest.mark.parametrize(("rule", "table", "change"), CASES, ids=[case[0] for case in CASES])
def test_reference_rule_fails(tmp_path: Path, rule: str, table: str, change) -> None:
    sample = SampleCopy(tmp_path)
    sample.edit(table, change)
    report = sample.reports()[rule]
    assert report.is_failed(), report


def test_ref306_point_labels(tmp_path: Path) -> None:
    """A LiDAR `label` value that no category index has fails."""
    sample = SampleCopy(tmp_path)
    sample.write_labels([[7] * 8] * 3)
    report = sample.reports()["REF306"]
    assert report.is_failed() and "[7]" in report.reasons[0]
