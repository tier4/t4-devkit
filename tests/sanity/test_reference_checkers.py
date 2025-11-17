from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from t4_devkit.sanity.context import SanityContext
from t4_devkit.sanity.reference.ref001 import REF001
from t4_devkit.sanity.reference.ref002 import REF002
from t4_devkit.sanity.reference.ref003 import REF003
from t4_devkit.sanity.reference.ref004 import REF004
from t4_devkit.sanity.reference.ref005 import REF005
from t4_devkit.sanity.reference.ref006 import REF006
from t4_devkit.sanity.reference.ref007 import REF007
from t4_devkit.sanity.reference.ref008 import REF008
from t4_devkit.sanity.reference.ref009 import REF009
from t4_devkit.sanity.reference.ref010 import REF010
from t4_devkit.sanity.reference.ref011 import REF011
from t4_devkit.sanity.reference.ref012 import REF012
from t4_devkit.sanity.reference.ref013 import REF013
from t4_devkit.sanity.reference.ref014 import REF014

# Sample dataset root (non-versioned)
SAMPLE_ROOT = Path(__file__).parent.parent.joinpath("sample", "t4dataset")
ANNOTATION_DIR = SAMPLE_ROOT / "annotation"


def _copy_dataset(dst_root: Path) -> Path:
    """Copy the entire sample dataset tree into a destination root."""
    shutil.copytree(SAMPLE_ROOT, dst_root)
    return dst_root


def _load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, records: list[dict]) -> None:
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def _context(root: Path) -> SanityContext:
    return SanityContext.from_path(root.as_posix())


# ---------------------------------------------------------------------------
# Helper mutations for record reference failures
# ---------------------------------------------------------------------------


def _mutate_single_value(records: list[dict], key: str, new_value: str) -> list[dict]:
    """Replace the first record's key value with new_value (assuming key exists)."""
    mutated = [dict(r) for r in records]
    if mutated:
        mutated[0][key] = new_value
    return mutated


def _ensure_is_valid(records: list[dict]) -> list[dict]:
    """Add 'is_valid': True to all records if missing (for REF005 additional condition)."""
    out = []
    for r in records:
        nr = dict(r)
        nr.setdefault("is_valid", True)
        out.append(nr)
    return out


# ---------------------------------------------------------------------------
# PASS (valid references) tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "checker_cls",
    [
        REF001,
        REF002,
        REF003,
        REF004,
        REF006,
        REF007,
        REF008,
        REF009,
        REF010,
        REF011,
        REF013,
        REF014,
    ],
)
def test_reference_checkers_pass(checker_cls: type) -> None:
    """Check that reference-related checkers pass (or have no failures) on the sample dataset."""
    checker = checker_cls()
    report = checker(_context(SAMPLE_ROOT))
    # All are ERROR severity; a passed report should have no reasons.
    assert report.is_passed(strict=True), f"{checker_cls.__name__} expected to pass"
    if not report.is_skipped():
        assert report.reasons is None, f"{checker_cls.__name__} should have no reasons when passed"


def test_ref005_pass_with_is_valid(tmp_path: Path) -> None:
    """REF005 requires 'is_valid' field; augment sample_data.json."""
    # Copy dataset and inject is_valid=True to each sample_data record
    root = _copy_dataset(tmp_path / "dataset_ref005_pass")
    sd_path = root / "sample" / "t4dataset" / "annotation" / "sample_data.json"
    # In copied layout _copy_dataset copies SAMPLE_ROOT into root; SAMPLE_ROOT already ends with 't4dataset'
    # So annotation directory path is root/'annotation'.
    if not sd_path.exists():  # adjust if directory structure differs
        sd_path = root / "annotation" / "sample_data.json"
    records = _load_json(sd_path)
    _dump_json(sd_path, _ensure_is_valid(records))
    checker = REF005()
    report = checker(_context(root))
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_ref012_skipped_on_missing_sources() -> None:
    """REF012 should be skipped because lidarseg.json is optional and absent."""
    checker = REF012()
    report = checker(_context(SAMPLE_ROOT))
    assert report.is_skipped(), "REF012 should be skipped when source/target file missing"


# ---------------------------------------------------------------------------
# FAIL (invalid references) tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "checker_cls, filename, key_to_mutate, invalid_token",
    [
        (REF001, "scene.json", "log_token", "invalid_log_token"),
        (REF002, "scene.json", "first_sample_token", "invalid_first_sample"),
        (REF003, "scene.json", "last_sample_token", "invalid_last_sample"),
        (REF004, "sample.json", "scene_token", "invalid_scene_token"),
        (REF006, "sample_data.json", "ego_pose_token", "invalid_ego_pose_token"),
        (REF007, "sample_data.json", "calibrated_sensor_token", "invalid_calibrated_sensor_token"),
        (REF008, "calibrated_sensor.json", "sensor_token", "invalid_sensor_token"),
        (REF009, "instance.json", "category_token", "invalid_category_token"),
        (REF010, "instance.json", "first_annotation_token", "invalid_annotation_token"),
        (REF011, "instance.json", "last_annotation_token", "invalid_annotation_token"),
    ],
)
def test_reference_checkers_fail(
    checker_cls: type,
    filename: str,
    key_to_mutate: str,
    invalid_token: str,
    tmp_path: Path,
) -> None:
    """Create a mutated dataset with one invalid reference and assert the checker fails."""
    root = _copy_dataset(tmp_path / f"dataset_{checker_cls.__name__}_fail")
    # Adjust annotation path depending on copy layout
    ann_dir = root / "annotation"
    if not ann_dir.exists():
        # If _copy_dataset nested t4dataset under root
        ann_dir = root / "sample" / "t4dataset" / "annotation"
    target_file = ann_dir / filename
    records = _load_json(target_file)
    mutated = _mutate_single_value(records, key_to_mutate, invalid_token)
    # For sample_data invalid tests ensure is_valid exists (except those not involving REF005)
    if filename == "sample_data.json":
        mutated = _ensure_is_valid(mutated)
    _dump_json(target_file, mutated)

    checker = checker_cls()
    report = checker(_context(root))
    assert not report.is_passed(
        strict=True
    ), f"{checker_cls.__name__} should fail with invalid reference"
    assert report.reasons, "Failed report must include reasons"
    # Confirm invalid token mentioned somewhere
    assert any(invalid_token in r for r in report.reasons), "Invalid token should appear in reasons"


def test_ref005_fail_invalid_sample_reference(tmp_path: Path) -> None:
    """REF005 failure by breaking sample_data.sample_token while ensuring is_valid field exists."""
    root = _copy_dataset(tmp_path / "dataset_ref005_fail")
    ann_dir = root / "annotation"
    if not ann_dir.exists():
        ann_dir = root / "sample" / "t4dataset" / "annotation"

    sd_path = ann_dir / "sample_data.json"
    records = _load_json(sd_path)
    # ensure is_valid and mutate first sample_token
    mutated = _ensure_is_valid(records)
    if mutated:
        mutated[0]["sample_token"] = "nonexistent_sample_token"
    _dump_json(sd_path, mutated)

    checker = REF005()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons
    assert any("nonexistent_sample_token" in r for r in report.reasons)


def test_ref013_fail_missing_filename(tmp_path: Path) -> None:
    """Mutate sample_data.json to point to a missing file for REF013."""
    root = _copy_dataset(tmp_path / "dataset_ref013_fail")
    ann_dir = root / "annotation"
    if not ann_dir.exists():
        ann_dir = root / "sample" / "t4dataset" / "annotation"
    sd_path = ann_dir / "sample_data.json"
    records = _load_json(sd_path)
    if records:
        records[0]["filename"] = "data/CAM_FRONT/does_not_exist.jpg"
    _dump_json(sd_path, records)

    checker = REF013()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons
    assert any("does_not_exist.jpg" in r for r in report.reasons)


def test_ref014_fail_missing_info_filename(tmp_path: Path) -> None:
    """Add an info_filename pointing to a non-existing file to trigger REF014 failure."""
    root = _copy_dataset(tmp_path / "dataset_ref014_fail")
    ann_dir = root / "annotation"
    if not ann_dir.exists():
        ann_dir = root / "sample" / "t4dataset" / "annotation"
    sd_path = ann_dir / "sample_data.json"
    records = _load_json(sd_path)
    if records:
        records[0]["info_filename"] = "data/CAM_FRONT/missing_info.json"
    _dump_json(sd_path, records)

    checker = REF014()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons
    assert any("missing_info.json" in r for r in report.reasons)
