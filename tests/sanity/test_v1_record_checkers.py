from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import SampleCopy

set_field = SampleCopy.set_field


def _second_instance(records: list[dict]) -> list[dict]:
    return [*set_field(records, 0, index=5), dict(records[0], token="instance_other")]


def _declare_label_field(records: list[dict]) -> list[dict]:
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
    ("REC009", "sensor", lambda r: set_field(r, 1, index=0)),
    ("REC010", "instance", _second_instance),
    ("REC011", "sensor", _declare_label_field),
    ("REC012", "scene", lambda r: set_field(r, 0, nbr_samples=5)),
    ("REC013", "instance", lambda r: set_field(r, 0, nbr_annotations=2)),
    ("REC014", "object_ann", lambda r: set_field(r, 1, instance_token="instance_car")),
    ("REC015", "object_ann", lambda r: set_field(r, 0, orientation=1.0)),
    ("REC016", "sample_annotation", lambda r: set_field(r, 0, confidence=0.5)),
    ("REC017", "sample_annotation", lambda r: set_field(r, 1, provenance=None)),
    ("REC018", "sample", lambda r: set_field(r, 0, has_key_frame=False)),
    ("REC019", "sensor", lambda r: (r[0]["camera"]["video"].update(frame_count=3), r)[1]),
    ("REC020", "sample_data", lambda r: set_field(r, 0, fileformat="jpg")),
    ("REC021", "sample", lambda r: set_field(r, 1, timestamp=r[0]["timestamp"] - 1)),
    ("REC022", "ego_pose", lambda r: set_field(r, 0, timestamp=1_704_067_200)),
    ("REC023", "manifest", _capabilities(lambda c: c["modalities"]["camera"].append("CAM_BACK"))),
    ("REC024", "manifest", _capabilities(lambda c: c.update(route=False))),
    ("REC025", "vehicle", lambda r: set_field(r, 0, model="unknown")),
    ("REC026", "route", lambda r: set_field(r, 0, valid_until=r[0]["valid_from"])),
    ("REC027", "sensor", lambda r: set_field(r, 0, rotation=[2.0, 0.0, 0.0, 0.0])),
    ("REC028", "sample_data", lambda r: set_field(r, 0, is_key_frame=False)),
]


@pytest.mark.parametrize(("rule", "table", "change"), CASES, ids=[case[0] for case in CASES])
def test_record_rule_fails(tmp_path: Path, rule: str, table: str, change) -> None:
    sample = SampleCopy(tmp_path)
    sample.edit(table, change)
    report = sample.reports()[rule]
    assert not report.is_passed(strict=True), report
    assert report.reasons


@pytest.mark.parametrize(
    ("rule", "table", "change"),
    [
        ("REC012", "scene", lambda r: set_field(r, 0, nbr_samples=5)),
        (
            "REC013",
            "instance",
            lambda r: set_field(r, 0, nbr_annotations=1, last_annotation_token=None),
        ),
    ],
)
def test_record_rule_fix(tmp_path: Path, rule: str, table: str, change) -> None:
    """`fix` recomputes the values and updates the table's hash in `manifest.json`."""
    sample = SampleCopy(tmp_path)
    sample.edit(table, change)
    assert sample.reports(fix=True)[rule].fixed
    reports = sample.reports(checksum=True)
    assert reports[rule].is_passed(strict=True)
    assert reports["STR012"].is_passed(strict=True)


def test_rec029_point_labels(tmp_path: Path) -> None:
    """Category 0 must be `unpainted`, and a frame's labels are all null or none null."""
    sample = SampleCopy(tmp_path / "bad")
    sample.write_labels([[0] * 8, [1] * 7 + [None], None])
    sample.edit("category", lambda r: set_field(set_field(r, 0, index=1), 1, index=0))
    reasons = sample.reports()["REC029"].reasons
    assert "not 'unpainted'" in reasons[0]
    assert "frames [1]" in reasons[1]

    sample = SampleCopy(tmp_path / "ok")
    sample.write_labels([[0] * 8, [1] * 8, None])
    sample.edit(
        "category",
        lambda r: set_field(set_field(r, 0, index=1), 1, index=0, name="unpainted"),
    )
    assert sample.reports()["REC029"].is_passed(strict=True)
