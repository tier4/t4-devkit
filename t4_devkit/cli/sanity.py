from __future__ import annotations

from pathlib import Path

import typer
from tabulate import tabulate
from tqdm import tqdm

from t4_devkit.common.io import save_json
from t4_devkit.common.sanity import DBException, sanity_check
from t4_devkit.common.serialize import serialize_dataclasses

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
    return [
        sanity_check(db_root, revision=revision, include_warning=include_warning)
        for db_root in tqdm(Path(db_parent).glob("*"), desc=">>>Sanity checking...")
    ]


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
    output: str | None = typer.Option(None, "-o", "--output", help="Path to output JSON file."),
    revision: str | None = typer.Option(
        None, "-rv", "--revision", help="Specify if you want to check the specific version."
    ),
    include_warning: bool = typer.Option(
        False, "-iw", "--include-warning", help="Indicates whether to report any warnings."
    ),
) -> None:
    exceptions = _run_sanity_check(db_parent, revision=revision, include_warning=include_warning)

    if all(e.is_ok() for e in exceptions):
        print("✅ No exceptions occurred!!")
    else:
        print("⚠️  Encountered some exceptions!!")
        headers = ["DatasetID", "Version", "Status", "Message"]
        table = [[e.dataset_id, e.version, e.status, e.message] for e in exceptions]
        print(tabulate(table, headers=headers, tablefmt="pretty"))

    if output:
        serialized = serialize_dataclasses(exceptions)
        save_json(serialized, output)
