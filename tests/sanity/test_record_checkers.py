from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from t4_devkit.sanity.context import SanityContext
from t4_devkit.sanity.record.rec001 import REC001
from t4_devkit.sanity.record.rec002 import REC002
from t4_devkit.sanity.record.rec003 import REC003
from t4_devkit.sanity.record.rec004 import REC004
from t4_devkit.sanity.record.rec005 import REC005

# Base sample dataset root (contains all mandatory annotation json files with non-empty records)
SAMPLE_ROOT = Path(__file__).parent.parent.joinpath("sample", "t4dataset")
ANNOTATION_DIR = SAMPLE_ROOT / "annotation"


def _copy_dataset(dst_root: Path) -> Path:
    """Copy the entire sample dataset tree into a destination root."""
    shutil.copytree(SAMPLE_ROOT, dst_root)
    return dst_root


def _make_mutated_dataset(tmp_path: Path, mutations: dict[str, list[dict]]) -> Path:
    """
    Create a dataset root copying the sample dataset and then apply record mutations.

    mutations: mapping of filename (e.g. 'scene.json') to new list[dict] content.
    """
    dst_root = _copy_dataset(tmp_path / "mutated_dataset")
    ann_dir = dst_root / "annotation"
    for filename, new_records in mutations.items():
        target = ann_dir / filename
        with target.open("w", encoding="utf-8") as f:
            json.dump(new_records, f, indent=2)
    return dst_root


def _context(root: Path) -> SanityContext:
    return SanityContext.from_path(root.as_posix())


# ---------------- REC001 (scene-single) ----------------


def test_rec001_pass_single_scene() -> None:
    checker = REC001()
    report = checker(_context(SAMPLE_ROOT))
    assert report.is_passed(strict=True)
    assert report.reasons is None


@pytest.mark.parametrize("num_scenes", [0, 2])
def test_rec001_fail_scene_count(num_scenes: int, tmp_path: Path) -> None:
    original = json.loads((ANNOTATION_DIR / "scene.json").read_text(encoding="utf-8"))
    if num_scenes == 0:
        mutated = []
    else:
        # duplicate original first record to create 2 scenes (different token for uniqueness)
        first = original[0]
        duplicate = {**first, "token": "duplicate_scene_token"}
        mutated = [first, duplicate]
    root = _make_mutated_dataset(tmp_path, {"scene.json": mutated})
    checker = REC001()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons and report.reasons[0].startswith(
        "'Scene' must contain exactly one element"
    )


# ---------------- REC002 (sample-not-empty) ----------------


def test_rec002_pass_sample_not_empty() -> None:
    checker = REC002()
    report = checker(_context(SAMPLE_ROOT))
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_rec002_fail_sample_empty(tmp_path: Path) -> None:
    root = _make_mutated_dataset(tmp_path, {"sample.json": []})
    checker = REC002()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons and report.reasons[0] == "'Sample' record must not be empty"


# ---------------- REC003 (sample-data-not-empty) ----------------


def test_rec003_pass_sample_data_not_empty() -> None:
    checker = REC003()
    report = checker(_context(SAMPLE_ROOT))
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_rec003_fail_sample_data_empty(tmp_path: Path) -> None:
    root = _make_mutated_dataset(tmp_path, {"sample_data.json": []})
    checker = REC003()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons and report.reasons[0] == "'SampleData' record must not be empty"


# ---------------- REC004 (ego-pose-not-empty) ----------------


def test_rec004_pass_ego_pose_not_empty() -> None:
    checker = REC004()
    report = checker(_context(SAMPLE_ROOT))
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_rec004_fail_ego_pose_empty(tmp_path: Path) -> None:
    root = _make_mutated_dataset(tmp_path, {"ego_pose.json": []})
    checker = REC004()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons and report.reasons[0] == "'EgoPose' record must not be empty"


# ---------------- REC005 (calibrated-sensor-not-empty) ----------------


def test_rec005_pass_calibrated_sensor_not_empty() -> None:
    checker = REC005()
    report = checker(_context(SAMPLE_ROOT))
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_rec005_fail_calibrated_sensor_empty(tmp_path: Path) -> None:
    root = _make_mutated_dataset(tmp_path, {"calibrated_sensor.json": []})
    checker = REC005()
    report = checker(_context(root))
    assert not report.is_passed(strict=True)
    assert report.reasons and report.reasons[0] == "'CalibratedSensor' record must not be empty"
