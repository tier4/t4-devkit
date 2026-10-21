from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from t4_devkit.common.t4pack import (
    PackLayout,
    PackReader,
    decode_frame,
    encode_frame,
    find_pack,
    pack_directory,
    verify_pack,
    write_pack,
)


def _frame(num_points: int, num_pts_feats: int = 5, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    frame = rng.normal(0, 30, (num_points, num_pts_feats)).astype(np.float32)
    frame[:, 3] = rng.integers(0, 256, num_points)
    frame[:, 4] = rng.integers(-1, 128, num_points)
    return frame


def _write_frames(directory: Path, frames: list[np.ndarray], names: list[str]) -> None:
    directory.mkdir(parents=True)
    for frame, name in zip(frames, names, strict=True):
        frame.tofile(directory / name)


@pytest.mark.parametrize(
    ("num_pts_feats", "dtypes"),
    [
        (5, ("f4s", "f4s", "f4s", "u1", "i1")),
        (7, ("f4s", "f4s", "f4s", "u1", "i1", "u1", "f4s")),
        (6, ("f4s",) * 6),
    ],
)
def test_pack_layout_from_num_pts_feats(num_pts_feats: int, dtypes: tuple[str, ...]) -> None:
    layout = PackLayout.from_num_pts_feats(num_pts_feats)

    assert layout.dtypes == dtypes
    assert len(layout.fields) == num_pts_feats
    assert layout.fields[:4] == ("x", "y", "z", "intensity")


def test_pack_layout_rejects_too_few_features() -> None:
    with pytest.raises(ValueError):
        PackLayout.from_num_pts_feats(3)


@pytest.mark.parametrize("num_points", [0, 1, 1000])
def test_encode_decode_frame_round_trip(num_points: int) -> None:
    layout = PackLayout.from_num_pts_feats(5)
    frame = _frame(num_points)

    decoded = decode_frame(encode_frame(frame, layout.dtypes), layout.dtypes, num_points)

    assert np.array_equal(decoded, frame)


def test_encode_frame_rejects_wrong_width() -> None:
    with pytest.raises(ValueError):
        encode_frame(np.zeros((4, 4), dtype=np.float32), PackLayout.from_num_pts_feats(5).dtypes)


def test_write_and_read_pack(tmp_path: Path) -> None:
    filepath = tmp_path / "LIDAR_CONCAT.pack"
    layout = PackLayout.from_num_pts_feats(5)
    frames = [_frame(500, seed=0), _frame(0, seed=1), _frame(17, seed=2)]
    names = ["0.pcd.bin", "1.pcd.bin", "10.pcd.bin"]

    num_frames = write_pack(filepath, frames, layout=layout, names=names, level=1)

    assert num_frames == 3
    assert not (tmp_path / "LIDAR_CONCAT.pack.tmp").exists()
    with PackReader(filepath) as reader:
        assert len(reader) == 3
        assert reader.names == names
        assert reader.fields == list(layout.fields)
        for i, frame in enumerate(frames):
            assert np.array_equal(reader.read_frame(i), frame)
        assert np.array_equal(reader.read_frame_by_name("10.pcd.bin"), frames[2])
        with pytest.raises(IndexError):
            reader.read_frame(3)
        with pytest.raises(KeyError):
            reader.read_frame_by_name("2.pcd.bin")


def test_write_pack_names_frames_by_index_by_default(tmp_path: Path) -> None:
    filepath = tmp_path / "LIDAR_CONCAT.pack"
    frames = [_frame(10, seed=0), _frame(10, seed=1)]

    write_pack(filepath, frames, layout=PackLayout.from_num_pts_feats(5), level=1)

    with PackReader(filepath) as reader:
        assert reader.names == ["00000.pcd.bin", "00001.pcd.bin"]
        assert np.array_equal(reader.read_frame_by_name("00001.pcd.bin"), frames[1])


def test_write_pack_rejects_mismatched_names(tmp_path: Path) -> None:
    filepath = tmp_path / "LIDAR_CONCAT.pack"

    with pytest.raises(ValueError):
        write_pack(
            filepath,
            [_frame(10)],
            layout=PackLayout.from_num_pts_feats(5),
            names=["00000.pcd.bin", "00001.pcd.bin"],
        )
    assert not filepath.exists()
    assert not (tmp_path / "LIDAR_CONCAT.pack.tmp").exists()


def test_pack_reader_rejects_non_pack_file(tmp_path: Path) -> None:
    filepath = tmp_path / "junk.pack"
    filepath.write_bytes(b"not a pack at all")

    with pytest.raises(ValueError):
        PackReader(filepath)


def test_pack_directory_and_verify(tmp_path: Path) -> None:
    directory = tmp_path / "data" / "LIDAR_CONCAT"
    names = ["00000.pcd.bin", "00001.pcd.bin", "00002.pcd.bin"]
    frames = [_frame(100, seed=i) for i in range(len(names))]
    _write_frames(directory, frames, names)

    stats = pack_directory(directory, level=1)

    assert stats is not None
    assert stats.num_frames == 3
    assert stats.raw_bytes == sum(frame.nbytes for frame in frames)
    assert stats.ratio > 1.0
    assert (tmp_path / "data" / "LIDAR_CONCAT.pack").exists()
    assert verify_pack(directory) == []

    # already packed
    assert pack_directory(directory, level=1) is None
    assert pack_directory(directory, level=1, overwrite=True) is not None

    # a changed source frame is reported
    _frame(100, seed=99).tofile(directory / names[1])
    assert verify_pack(directory) == [names[1]]


def test_pack_directory_supports_wide_points(tmp_path: Path) -> None:
    directory = tmp_path / "LIDAR_CONCAT"
    frame = _frame(100, num_pts_feats=7)
    frame[:, 5] = 1.0
    _write_frames(directory, [frame], ["00000.pcd.bin"])

    pack_directory(directory, num_pts_feats=7, level=1)

    assert verify_pack(directory, num_pts_feats=7) == []


def test_pack_directory_refuses_lossy_pack(tmp_path: Path) -> None:
    directory = tmp_path / "LIDAR_CONCAT"
    frame = _frame(100)
    frame[0, 3] = 0.5  # intensity is not an integer
    _write_frames(directory, [frame], ["00000.pcd.bin"])

    with pytest.raises(ValueError):
        pack_directory(directory, level=1)
    assert list(tmp_path.glob("*.pack*")) == []


def test_pack_directory_requires_frames(tmp_path: Path) -> None:
    directory = tmp_path / "LIDAR_CONCAT"
    directory.mkdir()

    with pytest.raises(FileNotFoundError):
        pack_directory(directory)


def test_find_pack(tmp_path: Path) -> None:
    filepath = tmp_path / "LIDAR_CONCAT" / "00000.pcd.bin"

    assert find_pack(filepath) is None

    (tmp_path / "LIDAR_CONCAT.pack").touch()
    assert find_pack(filepath) == str(tmp_path / "LIDAR_CONCAT.pack")
