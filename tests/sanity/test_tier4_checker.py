from __future__ import annotations

from pathlib import Path

from t4_devkit.sanity.context import SanityContext
from t4_devkit.sanity.tier4.tiv001 import TIV001

# Path to the provided sample dataset (non-versioned).
SAMPLE_ROOT = Path(__file__).parent.parent.joinpath("sample", "t4dataset")


def _context(path: Path) -> SanityContext:
    """Helper to build a SanityContext from a path."""
    return SanityContext.from_path(path.as_posix())


def test_tiv001_pass() -> None:
    """
    TIV001 should PASS (Tier4 loads successfully) on the valid sample dataset.
    """
    checker = TIV001()
    report = checker(_context(SAMPLE_ROOT))
    assert report.is_passed(strict=True), "Expected TIV001 to pass on sample dataset"
    assert not report.is_skipped(), "Sample dataset should not be skipped"
    assert report.reasons is None, "Passed report must not contain reasons"


def test_tiv001_skip_missing_root(tmp_path: Path) -> None:
    """
    TIV001 should be SKIPPED when the dataset root path does not exist.
    """
    missing_root = tmp_path / "does_not_exist"  # intentionally not created
    checker = TIV001()
    report = checker(_context(missing_root))
    assert report.is_skipped(), "Expected TIV001 to be skipped for missing root directory"
    assert report.reasons, "Skipped report must include a reason"


def test_tiv001_fail_broken_dataset(tmp_path: Path) -> None:
    """
    TIV001 should FAIL when Tier4 cannot be initialized due to broken dataset contents.

    We create a dataset root with an 'annotation' directory containing an invalid JSON file
    to trigger a loading failure.
    """
    broken_root = tmp_path / "broken_dataset"
    annotation_dir = broken_root / "annotation"
    annotation_dir.mkdir(parents=True)
    # Create a mandatory schema file with invalid JSON to force a parsing error.
    scene_file = annotation_dir / "scene.json"
    scene_file.write_text("{ invalid json", encoding="utf-8")

    checker = TIV001()
    report = checker(_context(broken_root))

    assert not report.is_passed(strict=True), "Broken dataset should cause TIV001 to fail"
    assert not report.is_skipped(), "Existing root should not trigger skip"
    assert report.reasons, "Failed report must include reasons"
    assert any(
        "Failed to load Tier4" in r for r in report.reasons
    ), "Failure reason should indicate Tier4 load issue"
