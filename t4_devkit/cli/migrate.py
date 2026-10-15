from __future__ import annotations

import sys
from pathlib import Path

import typer

from t4_devkit.sanity import print_sanity_result, sanity_check
from t4_devkit.schema.v1 import V0Migrator

from .version import version_callback

cli = typer.Typer(
    name="t4migrate",
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
    data_root: str = typer.Argument(
        ..., help="0.x dataset: the <DATASET_ID>/<VERSION> directory with annotation/."
    ),
    output_dir: str = typer.Argument(
        ..., help="Directory to write the 1.0 dataset to, as <DATASET_ID>/<DATASET_VERSION>."
    ),
    dataset_version: int = typer.Option(
        ..., "-d", "--dataset-version", help="Version of the 1.0 dataset (given by Web.Auto)."
    ),
    dataset_id: str | None = typer.Option(
        None, "--dataset-id", help="Dataset ID, if not the 0.x dataset's."
    ),
    keep_images: bool = typer.Option(
        False,
        "--keep-images",
        help="Copy camera images as they are instead of encoding one AV1 video per channel.",
    ),
) -> None:
    source = Path(data_root)
    if dataset_id is None:
        # 0.x datasets live in <DATASET_ID>/<VERSION>
        dataset_id = source.parent.name if source.name.isdigit() else source.name
    output_root = Path(output_dir) / dataset_id / str(dataset_version)

    migrator = V0Migrator(source, output_root)
    manifest = migrator.migrate(dataset_id, dataset_version, keep_images=keep_images)
    typer.echo(f"Migrated {source} to {output_root}")
    for note in manifest.migration_notes or []:
        typer.echo(f"  - {note}")

    result = sanity_check(output_root.parent.as_posix(), revision=str(dataset_version))
    print_sanity_result(result)
    sys.exit(0 if result.is_passed() else 1)
