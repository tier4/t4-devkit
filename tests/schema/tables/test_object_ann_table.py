from t4_devkit.schema import ObjectAnn, serialize_schema, serialize_schemas


def test_object_ann_json(object_ann_json) -> None:
    """Test loading object ann from a json file."""
    schemas = ObjectAnn.from_json(object_ann_json)
    serialized = serialize_schemas(schemas)
    assert isinstance(serialized, list)


def test_object_ann(object_ann_dict) -> None:
    """Test loading object ann from a dictionary."""
    schema = ObjectAnn.from_dict(object_ann_dict)
    serialized = serialize_schema(schema)
    assert serialized == object_ann_dict


def test_new_object_ann(object_ann_dict) -> None:
    """Test generating object ann with a new token."""
    without_token = {k: v for k, v in object_ann_dict.items() if k != "token"}
    ret = ObjectAnn.new(without_token)
    # check the new token is not the same with the token in input data
    assert ret.token != object_ann_dict["token"]
