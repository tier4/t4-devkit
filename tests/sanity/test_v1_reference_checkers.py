from __future__ import annotations

import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from t4_devkit.sanity import sanity_check

SAMPLE_V1 = Path(__file__).parents[1] / "sample" / "t4dataset_v1"
LIDAR_FILE = "data/LIDAR_TOP/LIDAR_TOP.parquet"


def _copy_v1(tmp_path: Path) -> Path:
    data_root = tmp_path / "sample"  # named as the sample's `dataset_id`
    shutil.copytree(SAMPLE_V1, data_root)
    return data_root


def _edit(data_root: Path, name: str, change) -> None:
    path = data_root / "annotation" / f"{name}.json"
    path.write_text(json.dumps(change(json.loads(path.read_text()))))


def _set(records: list[dict], position: int, **fields) -> list[dict]:
    records[position].update(fields)
    return records


def _lidar(records: list[dict], **fields) -> list[dict]:
    """Edit the `lidar` block of the LiDAR sensor."""
    records[1]["lidar"].update(fields)
    return records


def _add_label_column(data_root: Path) -> None:
    """Add a `label` column whose values no category has."""
    path = data_root / LIDAR_FILE
    parquet = pq.ParquetFile(path)
    with pq.ParquetWriter(
        path.with_suffix(".tmp"), parquet.schema_arrow.append(pa.field("label", pa.uint8()))
    ) as writer:
        for i in range(parquet.num_row_groups):
            table = parquet.read_row_group(i)
            writer.write_table(
                table.append_column("label", pa.array([7] * table.num_rows, pa.uint8()))
            )
    path.with_suffix(".tmp").replace(path)


def _reports(data_root: Path) -> dict:
    return {report.id: report for report in sanity_check(data_root.as_posix()).reports}


MISSING = "0" * 32

# (rule, table, change): each change breaks what the rule checks.
CASES = [
    ("REF015", "sample_data", lambda r: _set(r, 0, sensor_token=MISSING)),
    ("REF016", "log", lambda r: _set(r, 0, vehicle_token=MISSING)),
    ("REF017", "log", lambda r: _set(r, 0, map_token=None)),
    ("REF018", "sample_annotation", lambda r: _set(r, 0, visibility_token=MISSING)),
    ("REF019", "object_ann", lambda r: _set(r, 0, category_token=MISSING)),
    ("REF020", "keypoint", lambda r: _set(r, 0, category_tokens=[MISSING])),
    ("REF021", "traffic_light", lambda r: _set(r, 0, object_ann_token=MISSING)),
    ("REF022", "route", lambda r: _set(r, 0, map_token=MISSING)),
    ("REF023", "scenario", lambda r: _set(r, 0, log_token=MISSING)),
    ("REF024", "caption", lambda r: _set(r, 0, scenario_token=MISSING)),
    ("REF025", "sensor", lambda r: _lidar(r, source_channels=["CAM_FRONT"])),
    ("REF107", "sample", lambda r: _set(r, 0, next=r[2]["token"])),
    ("REF108", "sample_data", lambda r: _set(r, 0, next=r[3]["token"])),
    ("REF204", "sample_data", lambda r: _set(r, 0, filename="data/CAM_FRONT/other.mp4")),
    ("REF205", "sensor", lambda r: (r[1]["lidar"]["fields"][3].update(dtype="float64"), r)[1]),
    (
        "REF206",
        "sample_data",
        lambda r: [{**x, "num_points": 99} if x["num_points"] else x for x in r],
    ),
    ("REF207", "map", lambda r: _set(r, 0, sha256="0" * 64)),
    ("REF302", "instance", lambda r: _set(r, 0, map_element={"id": 99999, "type": "way"})),
    ("REF303", "traffic_light", lambda r: _set(r, 0, regulatory_element_id=99999)),
    (
        "REF304",
        "route",
        lambda r: _set(
            r, 0, segments=[{"preferred_primitive_id": 99999, "primitive_ids": [99999]}]
        ),
    ),
    ("REF305", "sensor", lambda r: _lidar(r, source_channels=["LIDAR_TOP"])),
]


def test_v1_sample_passes_reference_rules() -> None:
    reports = _reports(SAMPLE_V1)
    rules = {rule for rule, *_ in CASES} | {"REF306"}
    assert all(reports[rule].is_passed(strict=True) for rule in rules)


@pytest.mark.parametrize(("rule", "table", "change"), CASES, ids=[case[0] for case in CASES])
def test_reference_rule_fails(tmp_path: Path, rule: str, table: str, change) -> None:
    data_root = _copy_v1(tmp_path)
    _edit(data_root, table, change)
    report = _reports(data_root)[rule]
    assert report.is_failed(), report


def test_ref306_point_labels(tmp_path: Path) -> None:
    """A LiDAR `label` value that no category index has fails."""
    data_root = _copy_v1(tmp_path)
    _add_label_column(data_root)
    report = _reports(data_root)["REF306"]
    assert report.is_failed() and "[7]" in report.reasons[0]
