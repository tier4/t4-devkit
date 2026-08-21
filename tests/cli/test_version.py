from __future__ import annotations

import importlib.metadata

import pytest
from typer import Typer
from typer.testing import CliRunner

from t4_devkit.cli.sanity import cli as sanity_cli
from t4_devkit.cli.visualize import cli as visualize_cli


@pytest.mark.parametrize(
    ("cli", "name"),
    [
        (sanity_cli, "t4sanity"),
        (visualize_cli, "t4viz"),
    ],
)
def test_version(cli: Typer, name: str) -> None:
    result = CliRunner().invoke(cli, ["--version"], prog_name=name)

    assert result.exit_code == 0
    assert result.output == f"{name}: {importlib.metadata.version('t4-devkit')}\n"
