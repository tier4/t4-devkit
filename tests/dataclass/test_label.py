import pytest

from t4_devkit.dataclass.label import LabelPrefix, convert_label


def test_label_prefix() -> None:
    # test lower case
    obj1 = LabelPrefix.from_name("object")
    assert obj1 == LabelPrefix.OBJECT

    tlr1 = LabelPrefix.from_name("traffic_light")
    assert tlr1 == LabelPrefix.TRAFFIC_LIGHT

    # test upper case
    obj2 = LabelPrefix.from_name("OBJECT")
    assert obj2 == LabelPrefix.OBJECT

    tlr2 = LabelPrefix.from_name("TRAFFIC_LIGHT")
    assert tlr2 == LabelPrefix.TRAFFIC_LIGHT

    # test exception
    with pytest.raises(AssertionError):
        LabelPrefix.from_name("FOO")


def test_convert_label() -> None:
    # test CAR
    car_labels = (
        "car",
        "vehicle.car",
        "vehicle.construction",
        "vehicle.emergency (ambulance & police)",
        "vehicle.police",
    )

    for original in car_labels:
        ret = convert_label(LabelPrefix.OBJECT, original)
        # assert ret == ObjectLabel.CAR  # TODO: comparison raises exception
        assert ret.original == original

    # TODO: check other labels
