from __future__ import annotations

import pytest

from t4_devkit.typing import Roi


def test_roi() -> None:
    # Test individual arguments
    roi = Roi(10, 20, 30, 40)  # (xmin, ymin, xmax, ymax)

    assert roi.offset == (10, 20)
    assert roi.size == (20, 20)
    assert roi.width == 20
    assert roi.height == 20
    assert roi.center == (20, 30)
    assert roi.area == 400

    # Test iterable inputs - should produce equivalent results
    roi_list = Roi([10, 20, 30, 40])
    roi_tuple = Roi((10, 20, 30, 40))

    # All should be equal
    assert roi == roi_list == roi_tuple

    # Test properties are the same
    assert roi_list.offset == (10, 20)
    assert roi_list.size == (20, 20)
    assert roi_list.width == 20
    assert roi_list.height == 20
    assert roi_list.center == (20, 30)
    assert roi_list.area == 400


def test_invalid_roi() -> None:
    _ = Roi(0, 0, 0, 0)  # No error
    _ = Roi([0, 0, 0, 0])  # No error with list

    with pytest.raises(ValueError):
        # expecting the length of roi is 4 (individual args)
        _ = Roi(10, 10, 20)

    with pytest.raises(ValueError):
        # expecting the length of roi is 4 (list)
        _ = Roi([10, 10, 20])

    with pytest.raises(ValueError):
        # expecting xmin <= xmax and ymin <= ymax (individual args)
        _ = Roi(100, 100, 10, 20)

    with pytest.raises(ValueError):
        # expecting xmin <= xmax and ymin <= ymax (list)
        _ = Roi([100, 100, 10, 20])
