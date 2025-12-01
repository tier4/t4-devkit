from __future__ import annotations

from t4_devkit.dataclass.label import SemanticLabel


def test_semantic_label() -> None:
    label = SemanticLabel("car", ["vehicle.car"])

    # check properties
    assert label.name == "car"
    assert label.attributes == ["vehicle.car"]

    # same instance
    assert label == label
    # same label name
    assert label == SemanticLabel("car")
    assert label == "car"
    # same label name, but different case
    assert label != SemanticLabel("Car")
    assert label != "Car"
    # different label name
    assert label != SemanticLabel("bike")
    assert label != "bike"
