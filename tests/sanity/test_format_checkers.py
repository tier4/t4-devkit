from __future__ import annotations

from pathlib import Path

import pytest

from t4_devkit.sanity.context import SanityContext

# Import all format field type checkers
from t4_devkit.sanity.format.fmt001 import FMT001
from t4_devkit.sanity.format.fmt002 import FMT002
from t4_devkit.sanity.format.fmt003 import FMT003
from t4_devkit.sanity.format.fmt004 import FMT004
from t4_devkit.sanity.format.fmt005 import FMT005
from t4_devkit.sanity.format.fmt006 import FMT006
from t4_devkit.sanity.format.fmt007 import FMT007
from t4_devkit.sanity.format.fmt008 import FMT008
from t4_devkit.sanity.format.fmt009 import FMT009
from t4_devkit.sanity.format.fmt010 import FMT010
from t4_devkit.sanity.format.fmt011 import FMT011
from t4_devkit.sanity.format.fmt012 import FMT012
from t4_devkit.sanity.format.fmt013 import FMT013
from t4_devkit.sanity.format.fmt014 import FMT014  # optional (lidarseg) - missing in sample
from t4_devkit.sanity.format.fmt015 import FMT015
from t4_devkit.sanity.format.fmt016 import FMT016
from t4_devkit.sanity.format.fmt017 import FMT017  # optional (keypoint) - missing in sample
from t4_devkit.sanity.format.fmt018 import FMT018

# Root of the provided sample dataset (non-versioned)
SAMPLE_ROOT = Path(__file__).parent.parent.joinpath("sample", "t4dataset")


def _context() -> SanityContext:
    return SanityContext.from_path(SAMPLE_ROOT.as_posix())


# All checkers expected to PASS on the sample dataset.
# Optional schemas (lidarseg, keypoint) are absent but considered PASS (not skipped) by logic.
ALL_FORMAT_CHECKERS: list[type] = [
    FMT001,
    FMT002,
    FMT003,
    FMT004,
    FMT005,
    FMT006,
    FMT007,
    FMT008,
    FMT009,
    FMT010,
    FMT011,
    FMT012,
    FMT013,
    FMT014,
    FMT015,
    FMT016,
    FMT017,
    FMT018,
]


@pytest.mark.parametrize("checker_cls", ALL_FORMAT_CHECKERS)
def test_format_checker_passes(checker_cls: type) -> None:
    """
    Each format field type checker should pass against the sample dataset.

    Behavior expectations:
      - Mandatory schema files exist and records convert cleanly => PASSED (no reasons).
      - Optional schema files (missing) => treated as PASSED (no reasons).
    """
    context = _context()
    checker = checker_cls()
    report = checker(context)
    # Must be passed strictly (no failures or warnings with reasons)
    assert report.is_passed(strict=True), f"{checker_cls.__name__} expected to pass"
    # For passed reports reasons must be None
    assert report.reasons is None, f"{checker_cls.__name__} should not produce reasons when passing"


def test_optional_missing_schemas_present_in_param_list() -> None:
    """Sanity guard: ensure we explicitly covered optional missing schemas."""
    optional_missing = {"FMT014": FMT014, "FMT017": FMT017}
    for name, cls in optional_missing.items():
        report = cls()(_context())
        assert report.is_passed(strict=True), f"{name} (missing optional file) should pass"
        assert report.reasons is None
