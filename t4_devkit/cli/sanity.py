from __future__ import annotations

from pathlib import Path

import typer
from tabulate import tabulate
from tqdm import tqdm

from t4_devkit.common.sanity import DBException, sanity_check

from .version import version_callback

cli = typer.Typer(
    name="t4sanity",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


def _run_sanity_check(
    db_parent: str,
    *,
    revision: str | None = None,
    include_warning: bool = False,
) -> list[DBException]:
    exceptions: list[DBException] = []

    db_dirs: list[Path] = Path(db_parent).glob("*")

    for db_root in tqdm(db_dirs, desc=">>>Sanity checking..."):
        result = sanity_check(db_root, revision=revision, include_warning=include_warning)
        if result:
            exceptions.append(result)
    return exceptions


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
    db_parent: str = typer.Argument(..., help="Path to parent directory of the databases."),
    revision: str | None = typer.Option(
        None, "-rv", "--revision", help="Specify if you want to check the specific version."
    ),
    include_warning: bool = typer.Option(
        False, "-iw", "--include-warning", help="Indicates whether to report any warnings."
    ),
) -> None:
    exceptions = _run_sanity_check(db_parent, revision=revision, include_warning=include_warning)

    headers = ["DatasetID", "Version", "Message"]
    table = [[e.dataset_id, e.version, e.message] for e in exceptions]

    print(tabulate(table, headers=headers, tablefmt="pretty"))
