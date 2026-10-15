from __future__ import annotations

import json
import os
import threading
from fractions import Fraction
from functools import lru_cache
from typing import Any, Iterable, Mapping, Sequence

import av
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pypcd4
from PIL import Image
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = (
    "load_json",
    "save_json",
    "load_pointcloud",
    "save_pointcloud",
    "load_image",
    "save_video",
    "V0_BIN_FIELDS",
)

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
        Arrays of shape (N,) keyed by field name, in file order. A `.parquet` column that is
        null on every point of the frame is left out.
    """
    filepath = os.fspath(filepath)
    if filepath.endswith(".parquet"):
        if frame_index is None:
            raise ValueError("frame_index is required for a .parquet file")
        mtime = os.stat(filepath).st_mtime_ns
        frame = _open_parquet(filepath, mtime, os.getpid()).read_row_group(
            frame_index, columns=columns
        )
        # a column null on every point (e.g. point labels of a frame without labels) is left out
        return {
            name: frame[name].to_numpy()
            for name in frame.column_names
            if frame.num_rows == 0 or frame[name].null_count < frame.num_rows
        }

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


def save_pointcloud(
    filepath: PathLike,
    frames: Iterable[Mapping[str, np.ndarray]],
    fields: Sequence[tuple[str, str]],
    *,
    compression: str = "zstd",
) -> int:
    """Save the frames of a LiDAR channel as one Parquet file, one row group per frame.

    Columns are `fields`, in order. Floats use BYTE_STREAM_SPLIT and no dictionary encoding, the
    smallest in the 1.0 benchmark; readers do not depend on it.

    Args:
        filepath (PathLike): `.parquet` file to write.
        frames (Iterable[Mapping[str, np.ndarray]]): Arrays of shape (N,) keyed by field name,
            one mapping per frame. A frame may have no points.
        fields (Sequence[tuple[str, str]]): (name, dtype) of each column, e.g. from
            `sensor.lidar.fields`.
        compression (str, optional): Parquet compression codec.

    Returns:
        The number of frames written.
    """
    schema = pa.schema([(name, pa.from_numpy_dtype(np.dtype(dtype))) for name, dtype in fields])
    floats = [field.name for field in schema if pa.types.is_floating(field.type)]
    num_frames = 0
    with pq.ParquetWriter(
        os.fspath(filepath),
        schema,
        compression=compression,
        use_dictionary=False,
        column_encoding={name: "BYTE_STREAM_SPLIT" for name in floats},
    ) as writer:
        for frame in frames:
            columns = [np.asarray(frame[name], dtype=dtype) for name, dtype in fields]
            # one row group per frame, also for a frame without points
            writer.write_table(
                pa.table(columns, schema=schema), row_group_size=max(len(columns[0]), 1)
            )
            num_frames += 1
    return num_frames


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


def save_video(
    filepath: PathLike,
    frames: Iterable[np.ndarray],
    frame_rate: int,
    *,
    preset: int = 6,
    crf: int = 26,
) -> dict[str, Any]:
    """Save the frames of a camera channel as one AV1 MP4 video, with PyAV's SVT-AV1.

    Every frame is a keyframe. The track timescale is the frame rate, so a frame's pts is its
    `frame_index`. Colors are YUV 4:2:0, full range, BT.601.

    Args:
        filepath (PathLike): `.mp4` file to write.
        frames (Iterable[np.ndarray]): RGB images of shape (H, W, 3), all the same size: uint8 for
            8-bit video, uint16 for 10-bit video.
        frame_rate (int): Frames per second.
        preset (int, optional): SVT-AV1 preset (speed vs size).
        crf (int, optional): SVT-AV1 quality (lower is better).

    Returns:
        The values of `sensor.camera.video`, except `path`.
    """
    os.environ.setdefault("SVT_LOG", "1")
    container = av.open(
        os.fspath(filepath),
        mode="w",
        options={"movflags": "+faststart", "video_track_timescale": str(frame_rate)},
    )
    stream = None
    num_frames = 0
    bit_depth, pixel_format = 8, "yuv420p"
    with container:
        for image in frames:
            if stream is None:
                # uint16 frames: 10-bit video
                if image.dtype == np.uint16:
                    bit_depth, pixel_format = 10, "yuv420p10le"
                stream = _add_video_stream(container, image, frame_rate, pixel_format, preset, crf)
            rgb = av.VideoFrame.from_ndarray(image, format="rgb48le" if bit_depth > 8 else "rgb24")
            frame = rgb.reformat(
                format=pixel_format,
                dst_colorspace=av.video.reformatter.Colorspace.ITU601,
                dst_color_range=av.video.reformatter.ColorRange.JPEG,
            )
            frame.pts = num_frames
            container.mux(stream.encode(frame))
            num_frames += 1
        if stream is not None:
            container.mux(stream.encode())
    return {
        "format": "av1_mp4",
        "codec_profile": f"svt-av1 preset{preset} crf{crf} intra",
        "pixel_format": f"{pixel_format} full-range bt601",
        "bit_depth": bit_depth,
        "frame_count": num_frames,
        "timescale": frame_rate,
    }


def _add_video_stream(
    container: av.container.OutputContainer,
    image: np.ndarray,
    frame_rate: int,
    pixel_format: str,
    preset: int,
    crf: int,
) -> av.video.stream.VideoStream:
    """The AV1 stream of a camera video, sized by its first image."""
    stream = container.add_stream("libsvtav1", rate=frame_rate)
    stream.height, stream.width = image.shape[:2]
    stream.pix_fmt = pixel_format
    stream.time_base = Fraction(1, frame_rate)
    context = stream.codec_context
    context.gop_size = 1  # every frame a keyframe
    context.options = {
        "preset": str(preset),
        "crf": str(crf),
        # all intra, no scene detection or film grain, quiet
        "svtav1-params": "pred-struct=0:scd=0:film-grain=0:fast-decode=2:lp=0:log-level=1",
    }
    # full range, BT.601 matrix, BT.709 primaries, sRGB transfer (FFmpeg enum values)
    context.color_range = 2
    context.colorspace = 5
    context.color_primaries = 1
    context.color_trc = 13
    return stream


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
