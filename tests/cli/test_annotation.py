from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from t4_devkit.cli.annotation import cli
from t4_devkit.schema import SchemaName


runner = CliRunner()


def _copy_sample_dataset(tmp_path: Path) -> Path:
    source = Path(__file__).parents[1] / "sample" / "t4dataset"
    destination = tmp_path / "t4dataset"
    shutil.copytree(source, destination)
    return destination


def _load_table(data_root: Path, schema: SchemaName) -> list[object]:
    with (data_root / "annotation" / schema.filename).open() as file:
        return json.load(file)


ANNOTATION_SCHEMAS = [schema for schema in SchemaName if schema.is_annotated()]


def test_clear_requires_confirmation(tmp_path: Path) -> None:
    data_root = _copy_sample_dataset(tmp_path)
    instances_before = _load_table(data_root, SchemaName.INSTANCE)

    result = runner.invoke(cli, ["clear", str(data_root)], input="n\n")

    assert result.exit_code == 1
    assert _load_table(data_root, SchemaName.INSTANCE) == instances_before


def test_clear_empties_annotation_tables(tmp_path: Path) -> None:
    data_root = _copy_sample_dataset(tmp_path)

    result = runner.invoke(cli, ["clear", str(data_root), "--force"])

    assert result.exit_code == 0, result.output
    for schema in ANNOTATION_SCHEMAS:
        assert _load_table(data_root, schema) == []


def test_clear_new_version_preserves_source(tmp_path: Path) -> None:
    data_root = _copy_sample_dataset(tmp_path)
    instances_before = _load_table(data_root, SchemaName.INSTANCE)

    result = runner.invoke(cli, ["clear", str(data_root), "--new-version", "--force"])

    assert result.exit_code == 0, result.output
    assert _load_table(data_root, SchemaName.INSTANCE) == instances_before
    assert _load_table(data_root / "0", SchemaName.INSTANCE) == []
