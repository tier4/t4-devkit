import tempfile
from pathlib import Path

import numpy as np
import pypcd4
import pytest

from t4_devkit.common.io import load_json, load_pointcloud, save_json

SAMPLE_PARQUET = Path(__file__).parents[1] / "sample/t4dataset_v1/data/LIDAR_TOP/LIDAR_TOP.parquet"


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
