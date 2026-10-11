from __future__ import annotations

import json
import os
import threading
from functools import lru_cache
from typing import Any, Sequence

import av
import numpy as np
import pyarrow.parquet as pq
import pypcd4
from PIL import Image
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ("load_json", "save_json", "load_pointcloud", "load_image", "V0_BIN_FIELDS")

# 0.x `.bin` layout: this list cut to `num_pts_feats`, all float32 (as written by the converter).
# `.bin` stores no names; these are the 1.0 names (0.x calls `channel` "ring"), all float32.
V0_BIN_FIELDS = ("x", "y", "z", "intensity", "channel", "return_type", "time_stamp")


def load_json(filename: PathLike) -> Any:
    """Load json data from specified filepath.

    Args:
        filename (PathLike): File path to .json file.

    Returns:
        Loaded data.
    """
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def save_json(data: Any, filename: PathLike) -> None:
    """Save data into json file.

    Args:
        data (Any): Data to be saved.
        filename (PathLike): File path to save as json.
    """
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_pointcloud(
    filepath: PathLike,
    *,
    frame_index: int | None = None,
    fields: Sequence[tuple[str, str]] | None = None,
    columns: Sequence[str] | None = None,
) -> dict[str, np.ndarray]:
    """Load one pointcloud frame as one array per point field, in the dtype stored in the file.

    The layout is read from the file itself (`.parquet`, `.pcd`), or from `fields` for `.bin`,
    which has no header. Compression and encodings are read from the file.

    Args:
        filepath (PathLike): `.parquet` file of a channel, or `.pcd` / `.bin` file of one frame.
        frame_index (int | None, optional): Frame to read from a `.parquet` file (one row group per frame).
        fields (Sequence[tuple[str, str]] | None, optional): (name, dtype) of each point field
            of a `.bin` file, in order, e.g. from `sensor.lidar.fields`.
        columns (Sequence[str] | None, optional): Fields to return; all fields if None.

    Returns:
        Arrays of shape (N,) keyed by field name, in file order.
    """
    filepath = os.fspath(filepath)
    if filepath.endswith(".parquet"):
        if frame_index is None:
            raise ValueError("frame_index is required for a .parquet file")
        mtime = os.stat(filepath).st_mtime_ns
        frame = _open_parquet(filepath, mtime, os.getpid()).read_row_group(
            frame_index, columns=columns
        )
        return {name: frame[name].to_numpy() for name in frame.column_names}

    if filepath.endswith(".pcd"):
        data = pypcd4.PointCloud.from_path(filepath).pc_data
    elif filepath.endswith(".bin"):
        if fields is None:
            raise ValueError("fields is required for a .bin file")
        data = np.fromfile(filepath, dtype=np.dtype(list(fields)))
    else:
        raise ValueError(f"Unexpected filetype: {filepath}")

    names = data.dtype.names if columns is None else columns
    return {name: data[name] for name in names}


@lru_cache(maxsize=32)
def _open_parquet(filepath: str, mtime: int, pid: int) -> pq.ParquetFile:
    """Open a Parquet file once per process and file version, memory-mapped.

    Reopening per frame re-reads the footer. `mtime` and `pid` are only part of the cache key,
    so a rewritten file or a forked worker gets its own handle.
    """
    return pq.ParquetFile(filepath, memory_map=True)


def load_image(filepath: PathLike, *, frame_index: int | None = None) -> np.ndarray:
    """Load one camera frame as an RGB image.

    With `frame_index`, the file is a video (one per channel) read with PyAV: container, codec,
    pixel format, bit depth, color range and matrix, and timing all come from the file.
    Without it, the file is one image per frame (`.jpg`, `.png`, ...) read with Pillow.

    Args:
        filepath (PathLike): Video file of a channel, or image file of one frame.
        frame_index (int | None, optional): Frame to read from a video file.

    Returns:
        Image of shape (H, W, 3); uint8, or uint16 for video stored with more than 8 bits.
    """
    filepath = os.fspath(filepath)
    if frame_index is None:
        with Image.open(filepath) as image:
            return np.asarray(image.convert("RGB"))

    mtime = os.stat(filepath).st_mtime_ns
    container = _open_video(filepath, mtime, os.getpid(), threading.get_ident())
    stream = container.streams.video[0]
    # Constant frame rate: frame i is shown at i / rate seconds after the first frame.
    pts = (stream.start_time or 0) + round(frame_index / (stream.average_rate * stream.time_base))
    # Seeks to the nearest keyframe at or before `pts` (the frame itself for intra-only video).
    container.seek(pts, stream=stream)
    for frame in container.decode(stream):
        if frame.pts == pts:
            # Decoded frames are YUV (e.g. yuv420p); convert to RGB at the stored bit depth so
            # 8 bits per channel -> "rgb24" (uint8), more (e.g. 10-bit yuv420p10le) ->
            # "rgb48le" (uint16). `components[0]` is the luma plane.
            bit_depth = frame.format.components[0].bits
            rgb_format = "rgb48le" if bit_depth > 8 else "rgb24"
            return frame.reformat(
                format=rgb_format,
                src_colorspace=frame.colorspace,
                src_color_range=frame.color_range,
            ).to_ndarray()
        if frame.pts > pts:
            break
    raise IndexError(f"Frame {frame_index} not found in {filepath}")


@lru_cache(maxsize=32)
def _open_video(filepath: str, mtime: int, pid: int, thread: int) -> av.container.InputContainer:
    """Open a video file once per process, thread and file version.

    A container keeps decoding state, so threads do not share one. `mtime`, `pid` and `thread`
    are only part of the cache key.
    """
    container = av.open(filepath)
    # One decoding thread: random access decodes one frame after each seek, where FFmpeg's
    # default threading only adds latency (2880x1860 AV1: ~30 ms/frame default, ~20 ms with 1).
    container.streams.video[0].codec_context.thread_count = 1
    return container
