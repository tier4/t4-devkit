from __future__ import annotations

import os
import os.path as osp
import sys
from glob import glob
from typing import Annotated

import typer
from rich.console import Console

from t4_devkit.common.t4pack import FRAME_SUFFIX, pack_directory, verify_pack
from t4_devkit.dataclass.pointcloud import PointCloudMetainfo
from t4_devkit.tier4 import load_metadata

from .version import version_callback

console = Console()

cli = typer.Typer(
    name="t4pack",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    pretty_exceptions_enable=False,
)


@cli.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show the application version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    pass


@cli.command("pack", help="Pack .pcd.bin frames of each channel into '<CHANNEL>.pack'.")
def pack(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to pack the specific version."
        ),
    ] = None,
    level: Annotated[int, typer.Option(..., "-l", "--level", help="zstd compression level.")] = 19,
    overwrite: Annotated[
        bool, typer.Option(..., "--overwrite", help="Overwrite existing packs.")
    ] = False,
) -> None:
    channel_dirs = _find_channel_dirs(data_root, revision)

    for channel_dir in channel_dirs:
        stats = pack_directory(
            channel_dir,
            num_pts_feats=_num_pts_feats(channel_dir),
            level=level,
            overwrite=overwrite,
        )
        if stats is None:
            console.print(f"[yellow]SKIP[/yellow] {channel_dir}: already packed")
        else:
            console.print(
                f"[green]PACKED[/green] {channel_dir}: {stats.num_frames} frames, "
                f"{stats.raw_bytes} -> {stats.packed_bytes} bytes ({stats.ratio:.2f}x)"
            )


@cli.command("verify", help="Verify that each '<CHANNEL>.pack' matches its .pcd.bin frames.")
def verify(
    data_root: Annotated[str, typer.Argument(help="Root directory path to the dataset.")],
    revision: Annotated[
        str | None,
        typer.Option(
            ..., "-rv", "--revision", help="Specify if you want to verify the specific version."
        ),
    ] = None,
) -> None:
    channel_dirs = [
        channel_dir
        for channel_dir in _find_channel_dirs(data_root, revision)
        if osp.exists(channel_dir + ".pack")
    ]
    if not channel_dirs:
        console.print("[red]No packs to verify[/red]")
        sys.exit(1)

    is_passed = True
    for channel_dir in channel_dirs:
        mismatches = verify_pack(channel_dir, num_pts_feats=_num_pts_feats(channel_dir))
        if mismatches:
            is_passed = False
            console.print(
                f"[red]FAILED[/red] {channel_dir}: {len(mismatches)} frames differ, "
                f"e.g. {mismatches[:3]}"
            )
        else:
            console.print(f"[green]VERIFIED[/green] {channel_dir}")

    sys.exit(0 if is_passed else 1)


def _find_channel_dirs(data_root: str, revision: str | None) -> list[str]:
    """Return directories under `data/` that contain .pcd.bin frames."""
    data_dir = osp.join(load_metadata(data_root, revision).data_root, "data")
    if not osp.isdir(data_dir):
        raise FileNotFoundError(f"Data directory is not found: {data_dir}")

    return sorted(
        osp.join(data_dir, name)
        for name in os.listdir(data_dir)
        if osp.isdir(osp.join(data_dir, name))
        and glob(osp.join(data_dir, name, f"*{FRAME_SUFFIX}"))
    )


def _num_pts_feats(channel_dir: str) -> int:
    """Return `num_pts_feats` from the metainfo in `<CHANNEL>_INFO/`, or 5 if there is none."""
    info_filepaths = sorted(glob(osp.join(f"{channel_dir}_INFO", "*.json")))
    if not info_filepaths:
        return 5
    return PointCloudMetainfo.from_file(info_filepaths[0]).num_pts_feats
