from __future__ import annotations

import pytest

from t4_devkit.dataclass.roi import Roi


def test_roi() -> None:
    # list item is converted to tuple internally
    roi = Roi(roi=[10, 20, 30, 40])  # (xmin, ymin, xmax, ymax)

    assert roi.offset == (10, 20)
    assert roi.size == (20, 20)
    assert roi.width == 20
    assert roi.height == 20
    assert roi.center == (20, 30)
    assert roi.area == 400


def test_invalid_roi() -> None:
    _ = Roi(roi=[0, 0, 0, 0])  # No error

    with pytest.raises(ValueError):
        # expecting the length of roi is 4
        _ = Roi(roi=[10, 10])

        # expecting xmin <= xmax and ymin <= ymax
        _ = Roi(roi=[100, 100, 10, 20])
