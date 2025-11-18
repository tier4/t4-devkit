from __future__ import annotations

import sys

import typer

from t4_devkit.common.io import save_json
from t4_devkit.common.serialize import serialize_dataclass
from t4_devkit.sanity import print_sanity_result, sanity_check

from .version import version_callback

cli = typer.Typer(
    name="t4sanity",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


@cli.command()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the application version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
    data_root: str = typer.Argument(..., help="Path to root directory of a dataset."),
    output: str | None = typer.Option(None, "-o", "--output", help="Path to output JSON file."),
    revision: str | None = typer.Option(
        None, "-rv", "--revision", help="Specify if you want to check the specific version."
    ),
    excludes: list[str] | None = typer.Option(
        None, "-e", "--exclude", help="Exclude specific rules or rule groups."
    ),
    strict: bool = typer.Option(
        False,
        "-s",
        "--strict",
        help="By default, warnings do not cause failure. If set, warnings are treated as failures.",
    ),
) -> None:
    result = sanity_check(data_root=data_root, revision=revision, excludes=excludes)

    print_sanity_result(result, strict=strict)

    if output:
        serialized = serialize_dataclass(result)
        save_json(serialized, output)

    if result.is_passed(strict=strict):
        sys.exit(0)
    else:
        sys.exit(1)
