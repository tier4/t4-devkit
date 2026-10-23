"""t4pack: a container that stores all pointcloud frames of a sensor channel in a single file.

Format (t4pack v1):

```
magic b'T4PACK\\x00\\x01'
blob_0 .. blob_{N-1}            zstd(column_0 bytes | column_1 bytes | ...)
zstd(JSON index)                name, offset, size, n_points, dtypes per frame
<QQ index_offset index_size>    little-endian
magic
```

Points are stored column-major, one contiguous plane per column. Float32 columns are
byte-shuffled (dtype code `f4s`): the four bytes of every float are split into four planes,
so the near-constant sign/exponent bytes are grouped together and zstd can match them.
Each frame is compressed independently, so reading one frame decodes only that frame.
"""

from __future__ import annotations

import json
import os
import os.path as osp
import struct
import uuid
from typing import TYPE_CHECKING, Iterable, Sequence

import numpy as np
import zstandard as zstd
from attrs import define

if TYPE_CHECKING:
    from typing_extensions import Self

    from t4_devkit.typing import NDArrayF32, PathLike

__all__ = (
    "PACK_SUFFIX",
    "PackLayout",
    "PackReader",
    "PackStats",
    "encode_frame",
    "decode_frame",
    "write_pack",
    "pack_directory",
    "verify_pack",
    "delete_loose_frames",
    "find_pack",
)

MAGIC = b"T4PACK\x00\x01"
TRAILER = struct.Struct("<QQ")

#: Suffix of a pack file, which is placed next to the directory of loose frames.
PACK_SUFFIX = ".pack"
#: Suffix of a loose pointcloud frame.
FRAME_SUFFIX = ".pcd.bin"


@define(frozen=True)
class PackLayout:
    """A dataclass to represent the column layout of points in a pack.

    Attributes:
        dtypes (tuple[str, ...]): t4pack dtype code of each column.
            `f4s` is byte-shuffled float32, `u1` is uint8 and `i1` is int8.
        fields (tuple[str, ...]): Name of each column.
    """

    dtypes: tuple[str, ...]
    fields: tuple[str, ...]

    @classmethod
    def from_num_pts_feats(cls, num_pts_feats: int) -> Self:
        """Return the layout for points with the specified number of float32 features.

        The 1-byte columns (`u1`, `i1`) are only valid when the source values are integers in range,
        which is guaranteed by verifying every frame after packing.
        Unknown widths are stored as byte-shuffled float32 columns, which is always lossless.

        Args:
            num_pts_feats (int): Number of float32 fields in each point.

        Returns:
            Self: Layout of columns.
        """
        if num_pts_feats == 5:
            return cls(
                dtypes=("f4s", "f4s", "f4s", "u1", "i1"),
                fields=("x", "y", "z", "intensity", "ring"),
            )
        elif num_pts_feats == 7:
            return cls(
                dtypes=("f4s", "f4s", "f4s", "u1", "i1", "u1", "f4s"),
                fields=("x", "y", "z", "intensity", "channel", "return_type", "timestamp"),
            )
        elif num_pts_feats >= 4:
            return cls(
                dtypes=("f4s",) * num_pts_feats,
                fields=("x", "y", "z", "intensity")
                + tuple(f"feature{i}" for i in range(4, num_pts_feats)),
            )
        else:
            raise ValueError(f"Expected num_pts_feats >= 4, but got {num_pts_feats}")

    def to_lossless(self) -> Self:
        """Return the layout that stores every column as byte-shuffled float32.

        Returns:
            Self: Lossless layout with the same fields.
        """
        return self.__class__(dtypes=("f4s",) * len(self.dtypes), fields=self.fields)


@define
class PackStats:
    """A dataclass to represent the result of packing frames.

    Attributes:
        num_frames (int): Number of packed frames.
        raw_bytes (int): Total size of the source frames in bytes.
        packed_bytes (int): Size of the pack file in bytes.
    """

    num_frames: int
    raw_bytes: int
    packed_bytes: int

    @property
    def ratio(self) -> float:
        """Return the compression ratio.

        Returns:
            float: `raw_bytes / packed_bytes`.
        """
        return self.raw_bytes / self.packed_bytes if self.packed_bytes else 0.0


def encode_frame(frame: NDArrayF32, dtypes: Sequence[str]) -> bytes:
    """Serialize one frame into an uncompressed blob.

    Args:
        frame (NDArrayF32): Points in the shape of (N, len(dtypes)).
        dtypes (Sequence[str]): t4pack dtype code of each column.

    Returns:
        bytes: Serialized column-major blob.
    """
    frame = np.asarray(frame, dtype=np.float32)
    if frame.ndim != 2 or frame.shape[1] != len(dtypes):
        raise ValueError(f"Expected frame shape is (N, {len(dtypes)}), but got {frame.shape}")

    parts = []
    for column, dtype in enumerate(dtypes):
        values = frame[:, column]
        if dtype == "f4s":
            planes = np.ascontiguousarray(values, np.float32).view(np.uint8).reshape(-1, 4)
            parts.append(np.ascontiguousarray(planes.T).tobytes())
        elif dtype == "u1":
            parts.append(values.astype(np.uint8).tobytes())
        elif dtype == "i1":
            parts.append(values.astype(np.int8).tobytes())
        else:
            raise ValueError(f"Unknown t4pack dtype at column {column}: {dtype}")
    return b"".join(parts)


def decode_frame(raw: bytes, dtypes: Sequence[str], num_points: int) -> NDArrayF32:
    """Deserialize an uncompressed blob into one frame. This is the inverse of `encode_frame`.

    Args:
        raw (bytes): Serialized column-major blob.
        dtypes (Sequence[str]): t4pack dtype code of each column.
        num_points (int): Number of points in the frame.

    Returns:
        NDArrayF32: Points in the shape of (num_points, len(dtypes)).
    """
    out = np.empty((num_points, len(dtypes)), dtype=np.float32)
    pos = 0
    for column, dtype in enumerate(dtypes):
        if dtype == "f4s":
            planes = np.frombuffer(raw, np.uint8, 4 * num_points, pos).reshape(4, num_points)
            out[:, column] = np.ascontiguousarray(planes.T).reshape(-1).view(np.float32)
            pos += 4 * num_points
        elif dtype == "u1":
            out[:, column] = np.frombuffer(raw, np.uint8, num_points, pos)
            pos += num_points
        elif dtype == "i1":
            out[:, column] = np.frombuffer(raw, np.int8, num_points, pos)
            pos += num_points
        else:
            raise ValueError(f"Unknown t4pack dtype at column {column}: {dtype}")

    if pos != len(raw):
        raise ValueError(f"Frame has {len(raw) - pos} trailing bytes")
    return out


def write_pack(
    filepath: PathLike,
    frames: Iterable[NDArrayF32],
    layout: PackLayout,
    names: Sequence[str] | None = None,
    level: int = 19,
) -> int:
    """Write frames into a single pack file.

    The pack is written to a unique temporary file in the same directory first and renamed,
    so an interrupted write never leaves a partial pack in place,
    and concurrent writers never share a temporary file.

    Args:
        filepath (PathLike): Path to the output pack file.
        frames (Iterable[NDArrayF32]): Frames in the shape of (N_i, len(layout.dtypes)).
        layout (PackLayout): Column layout of points.
        names (Sequence[str] | None, optional): File name of each frame, used to look up frames.
            If None, `<index:05d>.pcd.bin` is used.
        level (int, optional): zstd compression level.

    Returns:
        int: Number of written frames.
    """
    filepath = os.fspath(filepath)
    tmp_filepath = _make_tmp_file(filepath)
    compressor = zstd.ZstdCompressor(level=level)
    entries = []
    try:
        with open(tmp_filepath, "wb") as f:
            f.write(MAGIC)
            for index, frame in enumerate(frames):
                if names is not None and index >= len(names):
                    raise ValueError(f"Got more frames than {len(names)} names")
                frame = np.asarray(frame, dtype=np.float32)
                blob = compressor.compress(encode_frame(frame, layout.dtypes))
                entries.append(
                    {
                        "name": f"{index:05d}{FRAME_SUFFIX}" if names is None else names[index],
                        "offset": f.tell(),
                        "size": len(blob),
                        "n_points": int(frame.shape[0]),
                        "dtypes": list(layout.dtypes),
                    }
                )
                f.write(blob)

            if names is not None and len(names) != len(entries):
                raise ValueError(f"Got {len(names)} names for {len(entries)} frames")

            index_blob = compressor.compress(
                json.dumps(
                    {
                        "format": "t4pack",
                        "version": 1,
                        "n_frames": len(entries),
                        "fields": list(layout.fields),
                        "frames": entries,
                    },
                    separators=(",", ":"),
                ).encode()
            )
            index_offset = f.tell()
            f.write(index_blob)
            f.write(TRAILER.pack(index_offset, len(index_blob)))
            f.write(MAGIC)
        os.replace(tmp_filepath, filepath)
    finally:
        if osp.exists(tmp_filepath):
            os.remove(tmp_filepath)

    return len(entries)


class PackReader:
    """Random-access reader of a pack file.

    This is not thread-safe, because it holds one file descriptor and one zstd decompressor.
    Open one reader per thread.

    Examples:
        >>> from t4_devkit.common.t4pack import PackReader
        >>> with PackReader("data/LIDAR_CONCAT.pack") as reader:
        ...     points = reader.read_frame_by_name("00000.pcd.bin")
    """

    def __init__(self, filepath: PathLike) -> None:
        """Open a pack file and load its frame index.

        Args:
            filepath (PathLike): Path to the pack file.
        """
        self.filepath = os.fspath(filepath)
        self._fd = os.open(self.filepath, os.O_RDONLY)
        self._dctx = zstd.ZstdDecompressor()
        try:
            size = os.fstat(self._fd).st_size
            trailer_size = TRAILER.size + len(MAGIC)
            trailer = os.pread(self._fd, trailer_size, max(size - trailer_size, 0))
            if (
                len(trailer) != trailer_size
                or trailer[TRAILER.size :] != MAGIC
                or os.pread(self._fd, len(MAGIC), 0) != MAGIC
            ):
                raise ValueError(f"Not a t4pack file: {self.filepath}")

            index_offset, index_size = TRAILER.unpack(trailer[: TRAILER.size])
            index = json.loads(self._dctx.decompress(os.pread(self._fd, index_size, index_offset)))
            if index.get("format") != "t4pack" or index.get("version") != 1:
                raise ValueError(
                    f"Unsupported pack format: {index.get('format')}/{index.get('version')}"
                )

            self.frames: list[dict] = index["frames"]
            self.fields: list[str] | None = index.get("fields")
            if int(index["n_frames"]) != len(self.frames):
                raise ValueError(f"n_frames does not match the frame index: {self.filepath}")
            self._name_to_index = {frame["name"]: i for i, frame in enumerate(self.frames)}
        except Exception:
            self.close()
            raise

    def __len__(self) -> int:
        return len(self.frames)

    def __contains__(self, name: str) -> bool:
        return name in self._name_to_index

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    @property
    def names(self) -> list[str]:
        """Return the file name of each frame.

        Returns:
            list[str]: List of frame names in the stored order.
        """
        return [frame["name"] for frame in self.frames]

    def close(self) -> None:
        """Close the file descriptor."""
        fd = getattr(self, "_fd", -1)
        if fd >= 0:
            os.close(fd)
            self._fd = -1

    def read_frame(self, index: int) -> NDArrayF32:
        """Decode the frame at the specified index.

        Args:
            index (int): Index of the frame.

        Returns:
            NDArrayF32: Points in the shape of (N, num_columns).
        """
        if not 0 <= index < len(self.frames):
            raise IndexError(f"Frame index {index} is out of range [0, {len(self.frames)})")

        frame = self.frames[index]
        blob = os.pread(self._fd, int(frame["size"]), int(frame["offset"]))
        return decode_frame(
            self._dctx.decompress(blob), tuple(frame["dtypes"]), int(frame["n_points"])
        )

    def read_frame_by_name(self, name: str) -> NDArrayF32:
        """Decode the frame with the specified file name.

        Args:
            name (str): File name of the frame, e.g. `00000.pcd.bin`.

        Returns:
            NDArrayF32: Points in the shape of (N, num_columns).
        """
        if name not in self:
            raise KeyError(f"Frame '{name}' is not found in {self.filepath}")
        return self.read_frame(self._name_to_index[name])


def _make_tmp_file(filepath: str) -> str:
    """Create a unique temporary file next to the specified path and return its path.

    Unlike `tempfile.mkstemp`, the file is created with the default permissions under umask,
    so the pack renamed from it is readable by other users as the source frames are.
    """
    tmp_filepath = f"{filepath}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp"
    with open(tmp_filepath, "xb"):
        pass
    return tmp_filepath


def _load_frame(filepath: str, num_pts_feats: int) -> NDArrayF32:
    scan = np.fromfile(filepath, dtype=np.float32)
    if scan.size % num_pts_feats != 0:
        raise ValueError(f"{scan.size} floats is not a multiple of {num_pts_feats}: {filepath}")
    return scan.reshape((-1, num_pts_feats))


def _list_frames(directory: str) -> list[str]:
    return sorted(name for name in os.listdir(directory) if name.endswith(FRAME_SUFFIX))


def pack_directory(
    directory: PathLike,
    num_pts_feats: int = 5,
    level: int = 19,
    overwrite: bool = False,
) -> PackStats | None:
    """Pack all `.pcd.bin` frames in a directory into `<directory>.pack`.

    Every frame is verified bit-exact against its source before the pack is put in place,
    so a pack that exists is always complete. If the 1-byte columns of the layout cannot hold
    the source values, e.g. non-integer intensity, every column is stored as float32 instead.
    Source frames are not deleted here, use `delete_loose_frames` to delete them.

    It is safe to run concurrently on the same directory: each call writes and verifies
    its own temporary file, and the last verified pack is put in place atomically.

    Args:
        directory (PathLike): Path to the directory of `.pcd.bin` frames, e.g. `data/LIDAR_CONCAT`.
        num_pts_feats (int, optional): Number of float32 fields in each point.
        level (int, optional): zstd compression level.
        overwrite (bool, optional): Whether to overwrite an existing pack.

    Returns:
        PackStats | None: Result of packing, or None if a valid pack already exists.
    """
    directory = os.fspath(directory).rstrip(os.sep)
    pack_filepath = directory + PACK_SUFFIX

    names = _list_frames(directory) if osp.isdir(directory) else []

    if osp.exists(pack_filepath):
        try:
            with PackReader(pack_filepath) as reader:
                packed_names = reader.names
        except Exception:
            packed_names = None  # broken pack, rewrite it

        if packed_names is not None:
            if not overwrite:
                return None
            # frames whose source has been deleted would be lost by rewriting the pack
            if dropped := sorted(set(packed_names) - set(names)):
                raise ValueError(
                    f"Cannot overwrite {pack_filepath}, {len(dropped)} frames have no source, "
                    f"e.g. {dropped[:3]}"
                )

    if not names:
        raise FileNotFoundError(f"No {FRAME_SUFFIX} frames in {directory}")

    filepaths = [osp.join(directory, name) for name in names]
    layout = PackLayout.from_num_pts_feats(num_pts_feats)
    lossless_layout = layout.to_lossless()
    # try the compact layout first, and fall back to the lossless one if it does not round-trip
    candidates = [layout] if layout == lossless_layout else [layout, lossless_layout]

    # write to a temporary file, verify it, and then rename it to the final path
    tmp_filepath = _make_tmp_file(pack_filepath)
    try:
        for candidate in candidates:
            num_frames = write_pack(
                tmp_filepath,
                (_load_frame(filepath, num_pts_feats) for filepath in filepaths),
                layout=candidate,
                names=names,
                level=level,
            )
            mismatches = _compare_frames(tmp_filepath, directory, names, num_pts_feats)
            if not mismatches:
                break

        if mismatches:
            raise ValueError(
                f"{len(mismatches)} frames differ after packing {directory}, e.g. {mismatches[:3]}"
            )
        os.replace(tmp_filepath, pack_filepath)
    finally:
        if osp.exists(tmp_filepath):
            os.remove(tmp_filepath)

    return PackStats(
        num_frames=num_frames,
        raw_bytes=sum(osp.getsize(filepath) for filepath in filepaths),
        packed_bytes=osp.getsize(pack_filepath),
    )


def verify_pack(directory: PathLike, num_pts_feats: int = 5) -> list[str]:
    """Verify `<directory>.pack` against the `.pcd.bin` frames in the directory.

    A frame whose source exists must equal it bit-exact, a source frame must be in the pack,
    and a frame whose source has been deleted must be decodable.

    Args:
        directory (PathLike): Path to the directory of `.pcd.bin` frames, e.g. `data/LIDAR_CONCAT`.
        num_pts_feats (int, optional): Number of float32 fields in each point.

    Returns:
        list[str]: Names of the frames that are missing, differ or are broken.
            Empty if the pack is valid.
    """
    directory = os.fspath(directory).rstrip(os.sep)
    names = _list_frames(directory) if osp.isdir(directory) else []
    return _compare_frames(directory + PACK_SUFFIX, directory, names, num_pts_feats)


def _compare_frames(
    pack_filepath: str,
    directory: str,
    names: list[str],
    num_pts_feats: int,
) -> list[str]:
    mismatches = []
    with PackReader(pack_filepath) as reader:
        source_names = set(names)
        for index, name in enumerate(reader.names):
            if name in source_names:
                continue
            # the source frame has been deleted, so only check that the frame can be decoded
            try:
                reader.read_frame(index)
            except Exception:
                mismatches.append(name)

        for name in names:
            try:
                packed = reader.read_frame_by_name(name)
            except KeyError:
                mismatches.append(name)
                continue
            try:
                source = _load_frame(osp.join(directory, name), num_pts_feats)
            except FileNotFoundError:
                continue  # deleted by another process after listing, the frame is decodable
            if not _is_bit_exact(packed, source):
                mismatches.append(name)
    return mismatches


def _is_bit_exact(lhs: NDArrayF32, rhs: NDArrayF32) -> bool:
    """Return whether two arrays are identical bit by bit.

    Unlike `np.array_equal`, NaN equals NaN and -0.0 differs from 0.0.
    """
    return lhs.shape == rhs.shape and lhs.tobytes() == rhs.tobytes()


def delete_loose_frames(directory: PathLike, num_pts_feats: int = 5) -> int:
    """Delete the `.pcd.bin` frames in a directory after verifying `<directory>.pack`.

    Nothing is deleted unless every frame in the directory equals its frame in the pack,
    and only the frames that have been verified are deleted.
    The directory itself is removed if it becomes empty.
    It is safe to run concurrently on the same directory.

    Args:
        directory (PathLike): Path to the directory of `.pcd.bin` frames, e.g. `data/LIDAR_CONCAT`.
        num_pts_feats (int, optional): Number of float32 fields in each point.

    Returns:
        int: Number of deleted frames.
    """
    directory = os.fspath(directory).rstrip(os.sep)
    if not osp.exists(directory + PACK_SUFFIX):
        raise FileNotFoundError(f"Pack is not found: {directory + PACK_SUFFIX}")

    names = _list_frames(directory) if osp.isdir(directory) else []
    mismatches = _compare_frames(directory + PACK_SUFFIX, directory, names, num_pts_feats)
    if mismatches:
        raise ValueError(
            f"{len(mismatches)} frames differ from the pack of {directory}, e.g. {mismatches[:3]}"
        )

    num_deleted = 0
    for name in names:
        try:
            os.remove(osp.join(directory, name))
            num_deleted += 1
        except FileNotFoundError:
            pass  # deleted by another process

    try:
        os.rmdir(directory)
    except OSError:
        pass  # not empty, or removed by another process

    return num_deleted


def find_pack(filepath: PathLike) -> str | None:
    """Return the path to the pack containing the specified frame if it exists.

    For example, the pack of `data/LIDAR_CONCAT/00000.pcd.bin` is `data/LIDAR_CONCAT.pack`.

    Args:
        filepath (PathLike): Path to a frame file.

    Returns:
        str | None: Path to the pack file, or None if it does not exist.
    """
    pack_filepath = osp.dirname(os.fspath(filepath)) + PACK_SUFFIX
    return pack_filepath if osp.exists(pack_filepath) else None
