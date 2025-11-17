from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from t4_devkit.sanity.context import SanityContext
from t4_devkit.sanity.structure.str001 import STR001
from t4_devkit.sanity.structure.str002 import STR002
from t4_devkit.sanity.structure.str003 import STR003
from t4_devkit.sanity.structure.str004 import STR004
from t4_devkit.sanity.structure.str005 import STR005
from t4_devkit.sanity.structure.str006 import STR006
from t4_devkit.sanity.structure.str007 import STR007
from t4_devkit.sanity.structure.str008 import STR008
from t4_devkit.sanity.structure.str009 import STR009

# Base sample dataset (no version dir, no input_bag, has annotation/data/map/status.json, lanelet2_map.osm, no pointcloud_map.pcd)
SAMPLE_ROOT = Path(__file__).parent.parent.joinpath("sample", "t4dataset")


def _copy_dataset(src: Path, dst: Path) -> None:
    """Copy entire dataset tree from src to dst."""
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _build_context(root: Path) -> SanityContext:
    """Helper to build SanityContext from dataset root."""
    return SanityContext.from_path(root.as_posix())


# ---------- STR001 (version-dir-presence) ----------


def _make_versioned_dataset(tmp_path: Path) -> Path:
    """Create a dataset root that has a numeric version subdirectory."""
    root = tmp_path / "versioned_dataset"
    version_dir = root / "1"
    version_dir.mkdir(parents=True, exist_ok=True)
    # copy sample dataset contents into version_dir
    _copy_dataset(SAMPLE_ROOT, version_dir)
    return root


def test_str001_fail_without_version_dir() -> None:
    checker = STR001()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert report.reasons and "'version' directory" in report.reasons[0]


def test_str001_pass_with_version_dir(tmp_path: Path) -> None:
    checker = STR001()
    dataset_root = _make_versioned_dataset(tmp_path)
    context = _build_context(dataset_root)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


# ---------- STR002 (annotation-dir-presence) ----------


def _make_dataset_without_annotation(tmp_path: Path) -> Path:
    root = tmp_path / "no_annotation"
    root.mkdir(exist_ok=True)
    # minimal files: data, map, status.json
    shutil.copytree(SAMPLE_ROOT / "data", root / "data")
    shutil.copytree(SAMPLE_ROOT / "map", root / "map")
    shutil.copy(SAMPLE_ROOT / "status.json", root / "status.json")
    return root


def test_str002_pass_annotation_present() -> None:
    checker = STR002()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_str002_fail_annotation_missing(tmp_path: Path) -> None:
    checker = STR002()
    root = _make_dataset_without_annotation(tmp_path)
    context = _build_context(root)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert report.reasons and "annotation" in report.reasons[0]


# ---------- STR003 (data-dir-presence) ----------


def _make_dataset_without_data(tmp_path: Path) -> Path:
    root = tmp_path / "no_data"
    root.mkdir(exist_ok=True)
    shutil.copytree(SAMPLE_ROOT / "annotation", root / "annotation")
    shutil.copytree(SAMPLE_ROOT / "map", root / "map")
    shutil.copy(SAMPLE_ROOT / "status.json", root / "status.json")
    return root


def test_str003_pass_data_present() -> None:
    checker = STR003()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_str003_fail_data_missing(tmp_path: Path) -> None:
    checker = STR003()
    root = _make_dataset_without_data(tmp_path)
    context = _build_context(root)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert report.reasons and "data" in report.reasons[0]


# ---------- STR004 (map-dir-presence) ----------


def _make_dataset_without_map(tmp_path: Path) -> Path:
    root = tmp_path / "no_map"
    root.mkdir(exist_ok=True)
    shutil.copytree(SAMPLE_ROOT / "annotation", root / "annotation")
    shutil.copytree(SAMPLE_ROOT / "data", root / "data")
    shutil.copy(SAMPLE_ROOT / "status.json", root / "status.json")
    return root


def test_str004_pass_map_present() -> None:
    checker = STR004()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_str004_fail_map_missing(tmp_path: Path) -> None:
    checker = STR004()
    root = _make_dataset_without_map(tmp_path)
    context = _build_context(root)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert report.reasons and "map" in report.reasons[0]


# ---------- STR005 (bag-dir-presence) ----------


def _make_dataset_with_bag(tmp_path: Path) -> Path:
    root = tmp_path / "with_bag"
    _copy_dataset(SAMPLE_ROOT, root)
    (root / "input_bag").mkdir(exist_ok=True)
    return root


def test_str005_fail_bag_missing() -> None:
    checker = STR005()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    # Warning severity; strict=True should treat as failure
    assert not report.is_passed(strict=True)
    assert report.reasons and "input_bag" in report.reasons[0]


def test_str005_pass_bag_present(tmp_path: Path) -> None:
    checker = STR005()
    root = _make_dataset_with_bag(tmp_path)
    context = _build_context(root)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


# ---------- STR006 (status-json-presence) ----------


def _make_dataset_without_status(tmp_path: Path) -> Path:
    root = tmp_path / "no_status"
    root.mkdir(exist_ok=True)
    shutil.copytree(SAMPLE_ROOT / "annotation", root / "annotation")
    shutil.copytree(SAMPLE_ROOT / "data", root / "data")
    shutil.copytree(SAMPLE_ROOT / "map", root / "map")
    return root


def test_str006_pass_status_present() -> None:
    checker = STR006()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_str006_fail_status_missing(tmp_path: Path) -> None:
    checker = STR006()
    root = _make_dataset_without_status(tmp_path)
    context = _build_context(root)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert report.reasons and "status.json" in report.reasons[0]


# ---------- STR007 (schema-file-presence) ----------


def _make_dataset_missing_schema(tmp_path: Path, missing: str) -> Path:
    """Create dataset missing one mandatory schema file."""
    root = tmp_path / "missing_schema"
    _copy_dataset(SAMPLE_ROOT, root)
    to_remove = root / "annotation" / missing
    if to_remove.exists():
        to_remove.unlink()
    return root


@pytest.mark.parametrize("missing_file", ["sample.json", "scene.json", "sensor.json"])
def test_str007_fail_missing_mandatory_schema(tmp_path: Path, missing_file: str) -> None:
    checker = STR007()
    root = _make_dataset_missing_schema(tmp_path, missing_file)
    context = _build_context(root)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert any(missing_file.replace(".json", "") in r for r in report.reasons)


def test_str007_pass_all_mandatory_present() -> None:
    checker = STR007()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


# ---------- STR008 (lanelet-file-presence) ----------


def _make_dataset_missing_lanelet(tmp_path: Path) -> Path:
    root = tmp_path / "missing_lanelet"
    _copy_dataset(SAMPLE_ROOT, root)
    lanelet_file = root / "map" / "lanelet2_map.osm"
    if lanelet_file.exists():
        lanelet_file.unlink()
    return root


def test_str008_pass_lanelet_present() -> None:
    checker = STR008()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None


def test_str008_fail_lanelet_missing(tmp_path: Path) -> None:
    checker = STR008()
    root = _make_dataset_missing_lanelet(tmp_path)
    context = _build_context(root)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert report.reasons and "Lanelet2 map file not found" in report.reasons[0]


# ---------- STR009 (pointcloud-map-dir-presence) ----------


def _make_dataset_with_pointcloud_map(tmp_path: Path) -> Path:
    root = tmp_path / "with_pointcloud_map"
    _copy_dataset(SAMPLE_ROOT, root)
    # Create an empty file to satisfy existence check
    (root / "map" / "pointcloud_map.pcd").write_text("")
    return root


def test_str009_fail_pointcloud_map_missing() -> None:
    checker = STR009()
    context = _build_context(SAMPLE_ROOT)
    report = checker(context)
    assert not report.is_passed(strict=True)
    assert report.reasons and "PCD map directory not found" in report.reasons[0]


def test_str009_pass_pointcloud_map_present(tmp_path: Path) -> None:
    checker = STR009()
    root = _make_dataset_with_pointcloud_map(tmp_path)
    context = _build_context(root)
    report = checker(context)
    assert report.is_passed(strict=True)
    assert report.reasons is None
