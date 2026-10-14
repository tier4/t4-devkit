from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from t4_devkit.sanity import sanity_check
from t4_devkit.sanity.checker import SchemaVersion
from t4_devkit.sanity.registry import CHECKERS

SAMPLE_ROOT = Path(__file__).parents[1] / "sample"
SAMPLE_V0 = SAMPLE_ROOT / "t4dataset"
SAMPLE_V1 = SAMPLE_ROOT / "t4dataset_v1"


def _reports(data_root: Path, **kwargs) -> dict:
    return {report.id: report for report in sanity_check(data_root.as_posix(), **kwargs).reports}


def _failed(reports: dict) -> set[str]:
    return {id for id, report in reports.items() if report.is_failed()}


def _copy_v1(tmp_path: Path) -> Path:
    data_root = tmp_path / "sample"  # named as the sample's `dataset_id`
    shutil.copytree(SAMPLE_V1, data_root)
    return data_root


def _edit_json(path: Path, change) -> None:
    path.write_text(json.dumps(change(json.loads(path.read_text()))))


def test_rules_by_version() -> None:
    """Each dataset gets only the rules of its version; 0.x keeps exactly its 0.x rules."""
    v0_rules = {
        id
        for rules in CHECKERS.values()
        for id, checker in rules.items()
        if SchemaVersion.V0 in checker.versions
    }
    assert set(_reports(SAMPLE_V0)) == v0_rules
    assert len(v0_rules) == 60

    v1_reports = _reports(SAMPLE_V1)
    assert "STR006" not in v1_reports and "FMT001" not in v1_reports
    assert {"STR001", "TIV001", "STR010", "FMT020", "FMT040"} <= set(v1_reports)


def test_v1_sample_passes(tmp_path: Path) -> None:
    """The 1.0 sample passes; the warnings are the missing version, bag and pointcloud map
    directories, and hashes not verified (opt-in)."""
    result = sanity_check(_copy_v1(tmp_path).as_posix())
    assert result.is_passed()
    warnings = {report.id for report in result.reports if not report.is_passed(strict=True)}
    assert warnings == {"STR001", "STR005", "STR009", "STR012"}


def test_str010_unsupported_version(tmp_path: Path) -> None:
    """An unsupported schema version fails, and the other 1.0 rules are skipped."""
    data_root = _copy_v1(tmp_path)
    _edit_json(data_root / "manifest.json", lambda m: {**m, "schema_version": "2.0.0"})
    reports = _reports(data_root)
    assert reports["STR010"].is_failed()
    assert reports["FMT020"].is_failed()
    assert reports["STR011"].is_skipped() and reports["FMT021"].is_skipped()


def test_str011_missing_file(tmp_path: Path) -> None:
    data_root = _copy_v1(tmp_path)
    (data_root / "map" / "lanelet2_map.osm").unlink()
    assert "STR011" in _failed(_reports(data_root))


def test_str012_checksum(tmp_path: Path) -> None:
    """Hashes are verified only with `checksum`; a changed file then fails."""
    data_root = _copy_v1(tmp_path)
    with (data_root / "map" / "lanelet2_map.osm").open("a") as f:
        f.write(" ")
    assert _reports(data_root)["STR012"].severity == "WARNING"
    report = _reports(data_root, checksum=True)["STR012"]
    assert report.is_failed() and "lanelet2_map.osm" in report.reasons[0]


def test_str013_unlisted_file(tmp_path: Path) -> None:
    data_root = _copy_v1(tmp_path)
    (data_root / "data" / "extra.txt").write_text("not listed")
    report = _reports(data_root)["STR013"]
    assert not report.is_passed(strict=True) and "data/extra.txt" in report.reasons[0]


def test_str014_required_table(tmp_path: Path) -> None:
    """An unlisted required table fails STR014, and its format rule is skipped."""
    data_root = _copy_v1(tmp_path)
    _edit_json(
        data_root / "manifest.json",
        lambda m: {**m, "tables": {k: v for k, v in m["tables"].items() if k != "vehicle"}},
    )
    reports = _reports(data_root)
    assert reports["STR014"].is_failed() and "vehicle" in reports["STR014"].reasons[0]
    assert reports["FMT027"].is_skipped()


def test_str015_identity(tmp_path: Path) -> None:
    data_root = tmp_path / "other_id"
    shutil.copytree(SAMPLE_V1, data_root)
    report = _reports(data_root)["STR015"]
    assert not report.is_passed(strict=True) and "'sample'" in report.reasons[0]


@pytest.mark.parametrize(
    ("table", "rule", "change"),
    [
        ("sensor", "FMT024", lambda records: [{**records[0], "index": 300}, *records[1:]]),
        ("sample", "FMT021", lambda records: [{**records[0], "prev": ""}, *records[1:]]),
    ],
)
def test_fmt_invalid_record(tmp_path: Path, table: str, rule: str, change) -> None:
    """A record that does not build into its 1.0 class fails its table's format rule."""
    data_root = _copy_v1(tmp_path)
    path = data_root / "annotation" / f"{table}.json"
    token = json.loads(path.read_text())[0]["token"]
    _edit_json(path, change)
    report = _reports(data_root)[rule]
    assert report.is_failed() and token in report.reasons[0]


def test_fmt_unreadable_table(tmp_path: Path) -> None:
    data_root = _copy_v1(tmp_path)
    (data_root / "annotation" / "scene.json").write_text("not json")
    report = _reports(data_root)["FMT025"]
    assert report.is_failed() and "cannot be read" in report.reasons[0]
