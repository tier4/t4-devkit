from __future__ import annotations

from pathlib import Path

from returns.maybe import Nothing, Some

from t4_devkit.sanity.context import SanityContext
from t4_devkit.schema import SchemaName


def test_sanity_context() -> None:
    """Test the sanity context function."""
    data_root = Path(__file__).parent.parent.joinpath("sample/t4dataset")
    context = SanityContext.from_path(data_root.as_posix())

    assert context.data_root == Some(data_root)
    assert context.dataset_id == Some("t4dataset")
    assert context.version == Nothing
    assert context.annotation_dir == Some(data_root.joinpath("annotation"))
    assert context.sensor_data_dir == Some(data_root.joinpath("data"))
    assert context.map_dir == Some(data_root.joinpath("map"))
    assert context.bag_dir == Some(data_root.joinpath("input_bag"))
    assert context.status_json == Some(data_root.joinpath("status.json"))

    for schema in SchemaName:
        assert context.to_schema_file(schema) == Some(
            data_root.joinpath("annotation", schema.filename)
        )
