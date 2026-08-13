from __future__ import annotations

from typing import Annotated, NoReturn

import typer
from returns.result import Failure, Success

from ..version import version_callback
from .clear import clear_annotations, plan_clear_annotations

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
    match plan_clear_annotations(
        data_root,
        revision=revision,
        new_version=new_version,
        exclude=exclude,
    ):
        case Success(plan):
            pass
        case Failure(error):
            _abort(str(error))

    if not new_version and not force:
        table_list = "\n".join(f"  - {schema.filename}" for schema in plan.schemas)
        typer.echo(
            "The following annotation record(s) will be cleared:\n"
            f"\nSource:\n  {plan.source_root}"
            f"\n\nTables:\n{table_list}\n"
        )
        typer.confirm("Continue?", abort=True)

    match clear_annotations(plan):
        case Success(result):
            pass
        case Failure(error):
            _abort(str(error))

    if result.version_created:
        typer.echo(f"Created version '{result.target_root.name}' at {result.target_root}")
    typer.echo("Cleared annotation record(s)")


def _abort(message: str) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(1)


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
