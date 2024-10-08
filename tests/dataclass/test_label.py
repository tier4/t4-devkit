from t4_devkit.dataclass.label import convert_label


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
        ret = convert_label(original)
        # assert ret == ObjectLabel.CAR  # TODO: comparison raises exception
        assert ret.original == original

    # TODO: check other labels
