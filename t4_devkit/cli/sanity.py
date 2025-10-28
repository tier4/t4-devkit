from __future__ import annotations

from pathlib import Path

import typer
from tabulate import tabulate
from tqdm import tqdm

from t4_devkit.common.io import save_json
from t4_devkit.common.serialize import serialize_dataclasses
from t4_devkit.sanity import SanityResult, sanity_check

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
    excludes: list[str] | None = None,
    include_warning: bool = False,
) -> list[SanityResult]:
    return [
        sanity_check(db_root, revision=revision, excludes=excludes, include_warning=include_warning)
        for db_root in tqdm(Path(db_parent).glob("*"), desc=">>>Sanity checking...")
    ]


def _print_table(results: list[SanityResult], *, detail: bool = False) -> str:
    summary_rows = []
    for result in results:
        success = sum(1 for rp in result.reports if rp.is_success())
        failures = sum(1 for rp in result.reports if rp.is_failure())
        skips = sum(1 for rp in result.reports if rp.is_skipped())
        summary_rows.append(
            [
                result.dataset_id,
                result.version,
                "\033[31mFAILURE\033[0m" if failures > 0 else "\033[32mSUCCESS\033[0m",
                len(result.reports),
                success,
                failures,
                skips,
            ]
        )

        if detail:
            print(result)

    print(f"\n{'=' * 40} Summary {'=' * 40}")
    print(
        tabulate(
            summary_rows,
            headers=["DatasetID", "Version", "Status", "Rules", "Success", "Failures", "Skips"],
            tablefmt="pretty",
        ),
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
    db_parent: str = typer.Argument(..., help="Path to parent directory of the databases."),
    output: str | None = typer.Option(None, "-o", "--output", help="Path to output JSON file."),
    revision: str | None = typer.Option(
        None, "-rv", "--revision", help="Specify if you want to check the specific version."
    ),
    excludes: list[str] | None = typer.Option(
        None, "-e", "--exclude", help="Exclude specific rules or rule groups."
    ),
    include_warning: bool = typer.Option(
        False, "-iw", "--include-warning", help="Indicates whether to report any warnings."
    ),
    detail: bool = typer.Option(
        False, "-d", "--detail", help="Indicates whether to display detailed reports."
    ),
) -> None:
    results = _run_sanity_check(
        db_parent,
        revision=revision,
        excludes=excludes,
        include_warning=include_warning,
    )

    _print_table(results, detail=detail)

    if output:
        serialized = serialize_dataclasses(results)
        save_json(serialized, output)
