from __future__ import annotations

import json
import os
import os.path as osp
import shutil
import tempfile
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from t4_devkit import T4Devkit
from t4_devkit.schema import SchemaName

from .version import version_callback

cli = typer.Typer(
    name="t4ann",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


@cli.command("clear", help="Clear the annotation records")
def clear(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to load the specific version."
        ),
    ] = None,
    new_version: Annotated[
        bool,
        typer.Option(
            ...,
            "-n",
            "--new-version",
            help="Create a new dataset version and clear its annotation records.",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(..., "-f", "--force", help="Force the clear operation without confirmation."),
    ] = False,
    exclude: Annotated[
        list[str] | None,
        typer.Option(..., "-e", "--exclude", help="Exclude specific schema names from clearing."),
    ] = None,
) -> None:
    """Clear annotation-related records while preserving the dataset structure."""

    def _abort(message: str) -> NoReturn:
        typer.echo(f"Error: {message}", err=True)
        raise typer.Exit(1)

    try:
        t4 = T4Devkit(data_root, revision=revision, verbose=False)
    except (FileNotFoundError, NotADirectoryError):
        _abort(f"Dataset root is not found: {data_root}")

    if not osp.isdir(t4.annotation_dir):
        _abort(f"Annotation directory is not found: {t4.annotation_dir}")

    excluded_schemas: set[SchemaName] = set()
    for name in exclude or []:
        try:
            schema = SchemaName(name.removesuffix(".json"))
        except ValueError:
            _abort(f"Unknown schema name: {name}")
        if not schema.is_annotated():
            _abort(f"Schema is not an annotation table: {name}")
        excluded_schemas.add(schema)

    annotated_schemas = [
        schema for schema in SchemaName if schema.is_annotated() and schema not in excluded_schemas
    ]
    target_root = _next_version_path(Path(data_root)) if new_version else Path(t4.data_root)

    if not new_version and not force:
        table_list = "\n".join(f"  - {schema.filename}" for schema in annotated_schemas)
        typer.echo(
            "The following annotation record(s) will be cleared:\n"
            f"\nSource:\n  {t4.data_root}"
            f"\n\nTables:\n{table_list}\n"
        )
        typer.confirm("Continue?", abort=True)

    if new_version:
        version_created = False
        try:
            _copy_version(Path(t4.data_root), target_root)
            version_created = True
            _clear_annotation_tables(target_root / "annotation", annotated_schemas)
        except OSError as error:
            if version_created:
                shutil.rmtree(target_root, ignore_errors=True)
            _abort(f"Failed to create version '{target_root.name}': {error}")
        typer.echo(f"Created version '{target_root.name}' at {target_root}")
    else:
        _clear_annotation_tables(Path(t4.annotation_dir), annotated_schemas)

    typer.echo("Cleared annotation record(s)")


def _next_version_path(data_root: Path) -> Path:
    """Return the path for the next numeric dataset version."""
    versions = [
        int(path.name) for path in data_root.iterdir() if path.is_dir() and path.name.isdigit()
    ]
    return data_root / str(max(versions, default=-1) + 1)


def _copy_version(source: Path, destination: Path) -> None:
    """Copy a dataset into a new version directory without recursively copying itself."""
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent.parent)
    )
    staging_version = staging_root / destination.name
    try:
        shutil.copytree(source, staging_version)
        os.replace(staging_version, destination)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def _clear_annotation_tables(annotation_dir: Path, annotated_schemas: list[SchemaName]) -> None:
    """Replace annotation tables with empty JSON arrays."""

    for schema in annotated_schemas:
        _save_empty_table(annotation_dir / schema.filename)


def _save_empty_table(filepath: Path) -> None:
    """Atomically replace an annotation table with an empty JSON array."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=filepath.parent, prefix=f".{filepath.name}.", delete=False
        ) as file:
            json.dump([], file, ensure_ascii=False, indent=4)
            file.write("\n")
            temporary_path = Path(file.name)
        os.replace(temporary_path, filepath)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


@cli.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the application version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    pass
