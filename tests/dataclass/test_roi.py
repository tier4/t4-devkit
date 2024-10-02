from t4_devkit.dataclass.roi import Roi


def test_roi() -> None:
    # list item is converted to tuple internally
    roi = Roi(roi=[10, 20, 30, 40])

    assert roi.offset == (10, 20)
    assert roi.size == (30, 40)
    assert roi.width == 30
    assert roi.height == 40
    assert roi.center == (25, 40)
    assert roi.area == 1200
