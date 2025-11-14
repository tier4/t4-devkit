from __future__ import annotations

from pathlib import Path

import pytest

from t4_devkit.sanity.run import sanity_check


@pytest.mark.parametrize("strict", [True, False])
def test_sanity_check(strict: bool) -> None:
    """Test the sanity check function."""
    data_root = Path(__file__).parent.parent.joinpath("sample/t4dataset")
    result = sanity_check(data_root.as_posix())

    if strict:
        assert result.is_passed(strict=strict) is False
    else:
        assert result.is_passed(strict=strict)
