from __future__ import annotations

import os
from typing import Annotated

import typer

from t4_devkit import Tier4

from .version import version_callback

cli = typer.Typer(
    name="t4viz",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


@cli.command("scene", help="Visualize a specific scene.")
def scene(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    future: Annotated[
        float,
        typer.Option(
            ...,
            "-f",
            "--future",
            help="Future time seconds.",
        ),
    ] = 0.0,
    output: Annotated[
        str | None,
        typer.Option(
            ...,
            "-o",
            "--output",
            help="Output directory to save recorded .rrd file.",
        ),
    ] = None,
) -> None:
    _create_dir(output)

    t4 = Tier4(data_root, verbose=False)
    t4.render_scene(future_seconds=future, save_dir=output)


@cli.command("instance", help="Visualize a particular instance in the corresponding scene.")
def instance(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    instance: Annotated[list[str], typer.Argument(help="Instance token(s).")],
    future: Annotated[
        float,
        typer.Option(
            ...,
            "-f",
            "--future",
            help="Future time seconds.",
        ),
    ] = 0.0,
    output: Annotated[
        str | None,
        typer.Option(
            ...,
            "-o",
            "--output",
            help="Output directory to save recorded .rrd file.",
        ),
    ] = None,
) -> None:
    _create_dir(output)

    t4 = Tier4(data_root, verbose=False)
    t4.render_instance(instance_token=instance, future_seconds=future, save_dir=output)


@cli.command("pointcloud", help="Visualize pointcloud in the corresponding scene.")
def pointcloud(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    ignore_distortion: Annotated[
        bool,
        typer.Option(
            ...,
            "-ig",
            "--ignore-distortion",
            help="Indicates whether to ignore camera distortion",
        ),
    ] = True,
    output: Annotated[
        str | None,
        typer.Option(
            ...,
            "-o",
            "--output",
            help="Output directory to save recorded .rrd file.",
        ),
    ] = None,
) -> None:
    _create_dir(output)

    t4 = Tier4(data_root, verbose=False)
    t4.render_pointcloud(ignore_distortion=ignore_distortion, save_dir=output)


def _create_dir(dir_path: str | None) -> None:
    """Create a directory with the specified path.

    If the input path is `None` this function does nothing.

    Args:
        dir_path (str | None): Directory path to create.
    """
    if dir_path is not None:
        os.makedirs(dir_path, exist_ok=True)


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
