from __future__ import annotations

import os

import click

from t4_devkit import Tier4


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
    else:
        ctx.invoked_subcommand


@main.command(name="scene", help="Visualize a specific scene.")
@click.argument("data_root", type=click.Path(exists=True))
@click.option("-f", "--future", type=float, default=0.0, help="Future time seconds.")
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True),
    help="Output directory to save recoding .rrd file.",
)
@click.option("--no-show", is_flag=True, help="Indicates whether not to show viewer.")
def scene(data_root: str, output: str | None, future: float, no_show: bool) -> None:
    _create_dir(output)

    t4 = Tier4("annotation", data_root, verbose=False)
    scene_token = t4.scene[0].token
    t4.render_scene(scene_token, future_seconds=future, save_dir=output, show=not no_show)


@main.command(name="instance", help="Visualize a particular instance in a corresponding scene")
@click.argument("data_root", type=click.Path(exists=True))
@click.argument("instance", type=click.STRING, nargs=-1)
@click.option("-f", "--future", type=float, default=0.0, help="Future time seconds.")
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True),
    help="Output directory to save recoding .rrd file.",
)
@click.option("--no-show", is_flag=True, help="Indicates whether not to show viewer.")
def instance(
    data_root: str,
    instance: tuple[str, ...],
    future: float,
    output: str | None,
    no_show: bool,
) -> None:
    _create_dir(output)

    t4 = Tier4("annotation", data_root, verbose=False)
    t4.render_instance(
        instance_token=instance, future_seconds=future, save_dir=output, show=not no_show
    )


@main.command(name="pointcloud", help="Visualize pointcloud in a corresponding scene.")
@click.argument("data_root", type=click.Path(exists=True))
@click.option(
    "-d",
    "--distortion",
    is_flag=True,
    help="Indicates whether not to ignore camera distortion.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True),
    help="Output directory to save recoding .rrd file.",
)
@click.option("--no-show", is_flag=True, help="Indicates whether not to show viewer.")
def pointcloud(data_root: str, distortion: bool, output: str | None, no_show: bool) -> None:
    _create_dir(output)

    t4 = Tier4("annotation", data_root, verbose=False)
    scene_token = t4.scene[0].token
    t4.render_pointcloud(
        scene_token,
        ignore_distortion=not distortion,
        save_dir=output,
        show=not no_show,
    )


def _create_dir(dir_path: str) -> None:
    """Create a directory with the specified path.
    If the input path is `None` this function does nothing.
    Args:
        dir_path (str | None): Directory path to create.
    """
    if dir_path is not None:
        os.makedirs(dir_path, exist_ok=True)
