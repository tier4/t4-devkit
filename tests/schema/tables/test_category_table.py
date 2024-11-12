from t4_devkit.schema import Category


def test_category_json(category_json) -> None:
    """Test loading category from a json file."""
    _ = Category.from_json(category_json)


def test_category(category_dict) -> None:
    """Test loading sample data from a dictionary."""
    _ = Category.from_dict(category_dict)
