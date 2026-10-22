from __future__ import annotations

from pathlib import Path

from t4_devkit.sanity import sanity_check
from t4_devkit.sanity.checker import SchemaVersion
from t4_devkit.sanity.registry import CHECKERS
from tests.helpers import SAMPLE_V0, SAMPLE_V1, SampleCopy


def test_rules_by_version() -> None:
    """Each dataset gets only the rules of its version; 0.x keeps exactly its 0.x rules."""
    v0_rules = {
        id
        for rules in CHECKERS.values()
        for id, checker in rules.items()
        if SchemaVersion.V0 in checker.versions
    }
    assert {report.id for report in sanity_check(SAMPLE_V0.as_posix()).reports} == v0_rules

    v1_reports = {report.id for report in sanity_check(SAMPLE_V1.as_posix()).reports}
    assert "STR006" not in v1_reports and "FMT001" not in v1_reports
    assert {"STR001", "TIV001", "STR010", "FMT020", "FMT040"} <= v1_reports


def test_v1_sample_passes(tmp_path: Path) -> None:
    """The 1.0 sample passes every rule, hashes included; the only warnings are the missing
    version, bag and pointcloud map directories."""
    result = sanity_check(SampleCopy(tmp_path).root.as_posix(), checksum=True)
    assert result.is_passed()
    warnings = {report.id for report in result.reports if not report.is_passed(strict=True)}
    assert warnings == {"STR001", "STR005", "STR009"}


def test_str010_unsupported_version(tmp_path: Path) -> None:
    """An unsupported schema version fails, and the other 1.0 rules are skipped."""
    sample = SampleCopy(tmp_path)
    sample.edit("manifest", lambda m: dict(m, schema_version="2.0.0"))
    reports = sample.reports()
    assert reports["STR010"].is_failed()
    assert reports["FMT020"].is_failed()
    assert reports["STR011"].is_skipped() and reports["FMT021"].is_skipped()


def test_str011_missing_file(tmp_path: Path) -> None:
    sample = SampleCopy(tmp_path)
    (sample.root / "map" / "lanelet2_map.osm").unlink()
    assert sample.reports()["STR011"].is_failed()


def test_str012_checksum(tmp_path: Path) -> None:
    """Hashes are verified only with `checksum`; a changed file then fails."""
    sample = SampleCopy(tmp_path)
    with (sample.root / "map" / "lanelet2_map.osm").open("a") as f:
        f.write(" ")
    assert sample.reports()["STR012"].severity == "WARNING"
    report = sample.reports(checksum=True)["STR012"]
    assert report.is_failed() and "lanelet2_map.osm" in report.reasons[0]


def test_str013_unlisted_file(tmp_path: Path) -> None:
    sample = SampleCopy(tmp_path)
    (sample.root / "data" / "extra.txt").write_text("not listed")
    report = sample.reports()["STR013"]
    assert not report.is_passed(strict=True) and "data/extra.txt" in report.reasons[0]


def test_str014_required_table(tmp_path: Path) -> None:
    """An unlisted required table fails STR014, and its format rule is skipped."""
    sample = SampleCopy(tmp_path)
    sample.edit(
        "manifest",
        lambda m: dict(m, tables={k: v for k, v in m["tables"].items() if k != "vehicle"}),
    )
    reports = sample.reports()
    assert reports["STR014"].is_failed() and "vehicle" in reports["STR014"].reasons[0]
    assert reports["FMT027"].is_skipped()


def test_str015_identity(tmp_path: Path) -> None:
    report = SampleCopy(tmp_path, name="other_id").reports()["STR015"]
    assert not report.is_passed(strict=True) and "'sample'" in report.reasons[0]


def test_fmt_invalid_record(tmp_path: Path) -> None:
    """A record that does not build into its 1.0 class fails its table's format rule."""
    sample = SampleCopy(tmp_path)
    token = sample.read("sensor")[0]["token"]
    sample.edit("sensor", lambda records: SampleCopy.set_field(records, 0, index=300))
    report = sample.reports()["FMT024"]
    assert report.is_failed() and token in report.reasons[0]


def test_fmt_unreadable_table(tmp_path: Path) -> None:
    sample = SampleCopy(tmp_path)
    (sample.root / "annotation" / "scene.json").write_text("not json")
    report = sample.reports()["FMT025"]
    assert report.is_failed() and "cannot be read" in report.reasons[0]
