import pytest

from t4_devkit.dataclass.shape import ShapeType


def test_shape_type() -> None:
    # test lower case
    bbox1 = ShapeType.from_name("bounding_box")
    assert bbox1 == ShapeType.BOUNDING_BOX

    polygon1 = ShapeType.from_name("polygon")
    assert polygon1 == ShapeType.POLYGON

    # test upper case
    bbox2 = ShapeType.from_name("BOUNDING_BOX")
    assert bbox2 == ShapeType.BOUNDING_BOX

    polygon1 = ShapeType.from_name("POLYGON")
    assert polygon1 == ShapeType.POLYGON

    # test exception
    with pytest.raises(AssertionError):
        ShapeType.from_name("FOO")
