from __future__ import annotations

import json
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from t4_devkit.sanity import sanity_check

SAMPLE_V1 = Path(__file__).parents[1] / "sample" / "t4dataset_v1"


def _copy_v1(tmp_path: Path) -> Path:
    data_root = tmp_path / "sample"  # named as the sample's `dataset_id`
    shutil.copytree(SAMPLE_V1, data_root)
    return data_root


def _edit(data_root: Path, name: str, change) -> None:
    """Edit a table (or `manifest`) of the copy in place."""
    path = data_root / ("manifest.json" if name == "manifest" else f"annotation/{name}.json")
    path.write_text(json.dumps(change(json.loads(path.read_text()))))


def _set(records: list[dict], position: int, **fields) -> list[dict]:
    records[position].update(fields)
    return records


def _reports(data_root: Path, **kwargs) -> dict:
    return {report.id: report for report in sanity_check(data_root.as_posix(), **kwargs).reports}


def _second_instance(records: list[dict]) -> list[dict]:
    return [*_set(records, 0, index=5), dict(records[0], token="instance_other")]


def _add_label_column(records: list[dict]) -> list[dict]:
    records[1]["lidar"]["fields"].append({"name": "label", "dtype": "uint8"})
    return records


def _capabilities(change):
    def edit(manifest: dict) -> dict:
        change(manifest["capabilities"])
        return manifest

    return edit


# (rule, table, change): each change breaks only what the rule checks.
CASES = [
    ("REC008", "sensor", lambda r: []),
    ("REC009", "sensor", lambda r: _set(r, 1, index=0)),
    ("REC010", "instance", _second_instance),
    ("REC011", "sensor", _add_label_column),
    ("REC012", "scene", lambda r: _set(r, 0, nbr_samples=5)),
    ("REC013", "instance", lambda r: _set(r, 0, nbr_annotations=2)),
    ("REC014", "object_ann", lambda r: _set(r, 1, instance_token="instance_car")),
    ("REC015", "object_ann", lambda r: _set(r, 0, orientation=1.0)),
    ("REC016", "sample_annotation", lambda r: _set(r, 0, confidence=0.5)),
    ("REC017", "sample_annotation", lambda r: _set(r, 1, provenance=None)),
    ("REC018", "sample", lambda r: _set(r, 0, has_key_frame=False)),
    ("REC019", "sensor", lambda r: (r[0]["camera"]["video"].update(frame_count=3), r)[1]),
    ("REC020", "sample_data", lambda r: _set(r, 0, fileformat="jpg")),
    ("REC021", "sample", lambda r: _set(r, 1, timestamp=r[0]["timestamp"] - 1)),
    ("REC022", "ego_pose", lambda r: _set(r, 0, timestamp=1_704_067_200)),
    ("REC023", "manifest", _capabilities(lambda c: c["modalities"]["camera"].append("CAM_BACK"))),
    ("REC024", "manifest", _capabilities(lambda c: c.update(route=False))),
    ("REC025", "vehicle", lambda r: _set(r, 0, model="unknown")),
    ("REC026", "route", lambda r: _set(r, 0, valid_until=r[0]["valid_from"])),
    ("REC027", "sensor", lambda r: _set(r, 0, rotation=[2.0, 0.0, 0.0, 0.0])),
    ("REC028", "sample_data", lambda r: _set(r, 0, is_key_frame=False)),
]


def test_v1_sample_passes_record_rules() -> None:
    reports = _reports(SAMPLE_V1)
    assert all(reports[rule].is_passed(strict=True) for rule, *_ in CASES)


@pytest.mark.parametrize(("rule", "table", "change"), CASES, ids=[case[0] for case in CASES])
def test_record_rule_fails(tmp_path: Path, rule: str, table: str, change) -> None:
    data_root = _copy_v1(tmp_path)
    _edit(data_root, table, change)
    report = _reports(data_root)[rule]
    assert not report.is_passed(strict=True), report
    assert report.reasons


@pytest.mark.parametrize(
    ("rule", "table", "change"),
    [
        ("REC012", "scene", lambda r: _set(r, 0, nbr_samples=5)),
        ("REC013", "instance", lambda r: _set(r, 0, nbr_annotations=1, last_annotation_token=None)),
    ],
)
def test_record_rule_fix(tmp_path: Path, rule: str, table: str, change) -> None:
    """`fix` recomputes the values and updates the table's hash in `manifest.json`."""
    data_root = _copy_v1(tmp_path)
    _edit(data_root, table, change)
    assert _reports(data_root, fix=True)[rule].fixed
    reports = _reports(data_root, checksum=True)
    assert reports[rule].is_passed(strict=True)
    assert reports["STR012"].is_passed(strict=True)


def _write_labels(data_root: Path, frames: list[list[int | None] | None]) -> None:
    """Add a `label` column to the LiDAR file and `sensor.json`; `None` = no labels."""
    path = data_root / "data/LIDAR_TOP/LIDAR_TOP.parquet"
    parquet = pq.ParquetFile(path)
    schema = parquet.schema_arrow.append(pa.field("label", pa.uint8()))
    with pq.ParquetWriter(path.with_suffix(".tmp"), schema) as writer:
        for i, labels in enumerate(frames):
            table = parquet.read_row_group(i)
            column = (
                pa.nulls(table.num_rows, pa.uint8())
                if labels is None
                else pa.array(labels, pa.uint8())
            )
            writer.write_table(table.append_column("label", column))
    path.with_suffix(".tmp").replace(path)
    _edit(data_root, "sensor", _add_label_column)


def test_rec029_point_labels(tmp_path: Path) -> None:
    """Category 0 must be `unpainted`, and a frame's labels are all null or none null."""
    data_root = _copy_v1(tmp_path)
    _write_labels(data_root, [[0] * 8, [1] * 7 + [None], None])
    _edit(data_root, "category", lambda r: _set(_set(r, 0, index=1), 1, index=0))

    reasons = _reports(data_root)["REC029"].reasons
    assert "not 'unpainted'" in reasons[0]
    assert "frames [1]" in reasons[1]

    _write_labels(_copy_v1(tmp_path / "ok"), [[0] * 8, [1] * 8, None])
    data_root = tmp_path / "ok" / "sample"
    _edit(data_root, "category", lambda r: _set(_set(r, 0, index=1), 1, index=0, name="unpainted"))
    assert _reports(data_root)["REC029"].is_passed(strict=True)
