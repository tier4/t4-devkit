from __future__ import annotations

import re
import warnings
from pathlib import Path

import typer
from attrs import define
from tabulate import tabulate

from t4_devkit import Tier4

from .version import version_callback


@define
class DBException:
    dataset_id: str
    version: str | None
    message: str


cli = typer.Typer(
    name="t4sanity",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


def _check_sanity(db_parent: str) -> list[DBException]:
    exceptions: list[DBException] = []

    db_dirs: list[Path] = Path(db_parent).glob("*")
    version_pattern = re.compile(r".*/\d+$")

    for db_root in db_dirs:
        versions = [d.name for d in db_root.iterdir() if version_pattern.match(str(d))]
        if versions:
            version = sorted(versions)[-1]
            data_root = db_root.joinpath(version).as_posix()
        else:
            version = None
            data_root = db_root.as_posix()

        try:
            _ = Tier4("annotation", data_root=data_root, verbose=False)
        except Exception as e:
            exceptions.append(
                DBException(
                    dataset_id=db_root.name,
                    version=version,
                    message=str(e),
                )
            )
        except Warning as w:
            exceptions.append(
                DBException(
                    dataset_id=db_root.name,
                    version=version,
                    message=str(w),
                )
            )
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
    db_parent: str = typer.Argument(..., help="Path to parent directory of the databases"),
    ignore_warning: bool = typer.Option(
        False, "-iw", "--ignore-warning", help="Indicates whether to ignore warnings"
    ),
) -> None:
    if ignore_warning:
        exceptions = _check_sanity(db_parent)
    else:
        with warnings.catch_warnings():
            exceptions = _check_sanity(db_parent)

    headers = ["DatasetID", "Version", "Message"]
    table = [[e.dataset_id, e.version, e.message] for e in exceptions]

    print(tabulate(table, headers=headers, tablefmt="pretty"))
