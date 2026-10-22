import tempfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pypcd4
import pytest
from PIL import Image

from t4_devkit.common.io import (
    load_image,
    load_json,
    load_pointcloud,
    save_json,
    save_pointcloud,
    save_video,
)

SAMPLE_PARQUET = Path(__file__).parents[1] / "sample/t4dataset_v1/data/LIDAR_TOP/LIDAR_TOP.parquet"
SAMPLE_VIDEO = Path(__file__).parents[1] / "sample/t4dataset_v1/data/CAM_FRONT/CAM_FRONT.mp4"


def test_json_io() -> None:
    """Test read/write json data."""
    data = {"foo": 1, "bar": [1, 2, 3, 4]}

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json(data, f.name)

        ret = load_json(f.name)

        assert ret == data


def test_load_pointcloud_parquet() -> None:
    """All fields come back in the dtype stored in the file; `columns` selects fields."""
    frame = load_pointcloud(SAMPLE_PARQUET, frame_index=1)
    assert list(frame) == ["x", "y", "z", "intensity", "ring"]
    assert frame["ring"].dtype == np.uint16
    assert len(frame["x"]) == 8

    assert list(load_pointcloud(SAMPLE_PARQUET, frame_index=0, columns=["x", "z"])) == ["x", "z"]

    with pytest.raises(ValueError, match="frame_index"):
        load_pointcloud(SAMPLE_PARQUET)


def test_load_pointcloud_parquet_null_column(tmp_path: Path) -> None:
    """A column null on every point of a frame (a frame without labels) is left out."""
    schema = pa.schema([("x", pa.float32()), ("label", pa.uint8())])
    path = tmp_path / "LIDAR_TOP.parquet"
    with pq.ParquetWriter(path, schema) as writer:
        writer.write_table(pa.table([pa.array([1.0, 2.0]), pa.array([0, 3])], schema=schema))
        writer.write_table(pa.table([pa.array([1.0, 2.0]), pa.nulls(2, pa.uint8())], schema=schema))

    labeled = load_pointcloud(path, frame_index=0)
    assert labeled["label"].tolist() == [0, 3]
    assert labeled["label"].dtype == np.uint8
    assert list(load_pointcloud(path, frame_index=1)) == ["x"]


def test_load_pointcloud_bin(tmp_path: Path) -> None:
    """A .bin file is read with the layout given in `fields`."""
    fields = [("x", "float32"), ("y", "float32"), ("z", "float32"), ("ring", "uint16")]
    data = np.array([(1, 2, 3, 7), (4, 5, 6, 8)], dtype=fields)
    data.tofile(tmp_path / "frame.bin")

    frame = load_pointcloud(tmp_path / "frame.bin", fields=fields)
    assert frame["ring"].tolist() == [7, 8]
    assert frame["z"].dtype == np.float32

    with pytest.raises(ValueError, match="fields"):
        load_pointcloud(tmp_path / "frame.bin")


def test_load_pointcloud_pcd(tmp_path: Path) -> None:
    """A .pcd file is read with the layout in its header."""
    points = np.arange(10, dtype=np.float32).reshape(2, 5)
    pypcd4.PointCloud.from_xyzir_points(points).save(tmp_path / "frame.pcd")

    frame = load_pointcloud(tmp_path / "frame.pcd")
    assert list(frame) == ["x", "y", "z", "intensity", "ring"]
    assert frame["ring"].dtype == np.uint16


def test_load_image_video() -> None:
    """Sample frames: red ramps 0..255 across the width, green is 128 * frame_index."""
    for frame_index in (1, 0):
        image = load_image(SAMPLE_VIDEO, frame_index=frame_index)
        assert image.shape == (48, 64, 3)
        assert image.dtype == np.uint8
        assert abs(image[..., 1].mean() - 128 * frame_index) < 4
        assert image[:, 0, 0].mean() < 8 and image[:, -1, 0].mean() > 240

    with pytest.raises(IndexError):
        load_image(SAMPLE_VIDEO, frame_index=2)


def test_load_image_file(tmp_path: Path) -> None:
    path = tmp_path / "frame.png"
    pixels = np.random.default_rng(0).integers(0, 256, (4, 6, 3), dtype=np.uint8)
    Image.fromarray(pixels).save(path)

    assert np.array_equal(load_image(path), pixels)


def test_save_pointcloud(tmp_path: Path) -> None:
    """Frames come back bit-exact in their dtypes, one row group each, empty frames included."""
    fields = [
        ("x", "float32"),
        ("intensity", "uint8"),
        ("channel", "uint16"),
        ("time_stamp", "uint32"),
    ]
    rng = np.random.default_rng(0)
    frames = [
        {
            "x": rng.normal(size=n).astype(np.float32),
            "intensity": rng.integers(0, 256, n).astype(np.uint8),
            "channel": rng.integers(0, 128, n).astype(np.uint16),
            "time_stamp": rng.integers(0, 100_000_000, n).astype(np.uint32),
        }
        for n in (5, 0, 3)
    ]
    path = tmp_path / "LIDAR_TOP.parquet"

    assert save_pointcloud(path, frames, fields) == 3
    for frame_index, expected in enumerate(frames):
        frame = load_pointcloud(path, frame_index=frame_index)
        assert list(frame) == [name for name, _ in fields]
        for name, dtype in fields:
            assert frame[name].dtype == np.dtype(dtype)
            assert np.array_equal(frame[name], expected[name])

    columns = pq.ParquetFile(path).metadata.row_group(0).to_dict()["columns"]
    encodings = {column["path_in_schema"]: column["encodings"] for column in columns}
    assert "BYTE_STREAM_SPLIT" in encodings["x"]
    assert "RLE_DICTIONARY" in encodings["intensity"]
    assert "DELTA_BINARY_PACKED" in encodings["channel"]
    assert "DELTA_BINARY_PACKED" in encodings["time_stamp"]


@pytest.mark.parametrize(
    ("dtype", "bit_depth", "max_value"), [(np.uint8, 8, 255), (np.uint16, 10, 65535)]
)
def test_save_video(tmp_path: Path, dtype, bit_depth: int, max_value: int) -> None:
    """Frames read back by index, in any order, close to what was written."""
    images = []
    for i in range(3):
        image = np.zeros((48, 64, 3), dtype=dtype)
        image[..., 0] = np.linspace(0, max_value, 64).astype(dtype)
        image[..., 1] = max_value // 4 * i
        images.append(image)
    path = tmp_path / "CAM_FRONT.mp4"

    video = save_video(path, iter(images), frame_rate=10)
    assert video["frame_count"] == 3 and video["timescale"] == 10
    assert video["bit_depth"] == bit_depth
    for frame_index in (2, 0, 1):
        image = load_image(path, frame_index=frame_index)
        assert image.dtype == dtype and image.shape == (48, 64, 3)
        # lossy, but the green level of each frame is kept
        green = image[..., 1].mean() / max_value
        assert abs(green - 0.25 * frame_index) < 0.03


def test_save_pointcloud_null_column(tmp_path: Path) -> None:
    """A field that is None in a frame is written null and left out when read."""
    fields = [("x", "float32"), ("label", "uint8")]
    frames = [
        {"x": np.array([1.0, 2.0], dtype=np.float32), "label": np.array([0, 3], dtype=np.uint8)},
        {"x": np.array([4.0], dtype=np.float32), "label": None},
    ]
    path = tmp_path / "LIDAR_TOP.parquet"

    assert save_pointcloud(path, frames, fields) == 2
    assert load_pointcloud(path, frame_index=0)["label"].tolist() == [0, 3]
    assert list(load_pointcloud(path, frame_index=1)) == ["x"]

    # what the reader returns can be written back as it is
    again = tmp_path / "again.parquet"
    save_pointcloud(again, [load_pointcloud(path, frame_index=i) for i in range(2)], fields)
    assert list(load_pointcloud(again, frame_index=1)) == ["x"]
