from t4_devkit.schema import Attribute


def test_attribute_json(attribute_json) -> None:
    """Test loading attribute from a json file."""
    _ = Attribute.from_json(attribute_json)


def test_attribute(attribute_dict) -> None:
    """Test loading attribute from a dictionary."""
    _ = Attribute.from_dict(attribute_dict)
