from t4_devkit.schema import ObjectAnn


def test_object_ann_json(object_ann_json) -> None:
    """Test loading object ann from a json file."""
    _ = ObjectAnn.from_json(object_ann_json)


def test_object_ann(object_ann_dict) -> None:
    """Test loading object ann from a dictionary."""
    _ = ObjectAnn.from_dict(object_ann_dict)
