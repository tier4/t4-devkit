from t4_devkit.schema import ObjectAnn


def test_object_ann_json(object_ann_json) -> None:
    """Test loading object ann from a json file."""
    _ = ObjectAnn.from_json(object_ann_json)


def test_object_ann(object_ann_dict) -> None:
    """Test loading object ann from a dictionary."""
    _ = ObjectAnn.from_dict(object_ann_dict)


def test_new_object_ann(object_ann_dict) -> None:
    """Test generating object ann with a new token."""
    without_token = {k: v for k, v in object_ann_dict.items() if k != "token"}
    ret = ObjectAnn.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != object_ann_dict["token"]
