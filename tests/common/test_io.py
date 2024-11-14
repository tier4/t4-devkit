import tempfile

from t4_devkit.common.io import load_json, save_json


def test_json_io() -> None:
    """Test read/write json data."""
    data = {"foo": 1, "bar": [1, 2, 3, 4]}

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json(data, f.name)

        ret = load_json(f.name)

        assert ret == data
