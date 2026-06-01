from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from t4_devkit.rosbag.pointcloud2 import pointcloud2_to_lidar


@dataclass
class MockPointField:
    """Mock of sensor_msgs/msg/PointField."""

    name: str
    offset: int
    datatype: int
    count: int = 1

    # PointField constants
    INT8: int = 1
    UINT8: int = 2
    INT16: int = 3
    UINT16: int = 4
    INT32: int = 5
    UINT32: int = 6
    FLOAT32: int = 7
    FLOAT64: int = 8


@dataclass
class MockPointCloud2:
    """Mock of sensor_msgs/msg/PointCloud2."""

    height: int
    width: int
    fields: list[MockPointField]
    is_bigendian: bool
    point_step: int
    row_step: int
    data: bytes
    is_dense: bool = True


def _build_pointcloud2(
    points: np.ndarray,
    field_names: list[str] | None = None,
) -> MockPointCloud2:
    """Build a mock PointCloud2 message from a numpy array.

    Args:
        points: (N, D) float32 array.
        field_names: Names for each column. Defaults to ["x", "y", "z", "intensity"].

    Returns:
        MockPointCloud2 message.
    """
    if field_names is None:
        field_names = ["x", "y", "z", "intensity"][: points.shape[1]]

    points = points.astype(np.float32)
    n_points = points.shape[0]
    n_fields = points.shape[1]
    point_step = n_fields * 4  # float32 = 4 bytes

    fields = [
        MockPointField(name=name, offset=i * 4, datatype=MockPointField.FLOAT32)
        for i, name in enumerate(field_names)
    ]

    return MockPointCloud2(
        height=1,
        width=n_points,
        fields=fields,
        is_bigendian=False,
        point_step=point_step,
        row_step=point_step * n_points,
        data=points.tobytes(),
    )


class TestPointCloud2ToLidar:
    def test_basic_conversion(self) -> None:
        points = np.array(
            [
                [1.0, 2.0, 3.0, 0.5],
                [4.0, 5.0, 6.0, 0.8],
                [7.0, 8.0, 9.0, 1.0],
            ],
            dtype=np.float32,
        )
        msg = _build_pointcloud2(points)

        result = pointcloud2_to_lidar(msg)

        assert result.points.shape == (4, 3)
        np.testing.assert_array_almost_equal(result.points[0], [1.0, 4.0, 7.0])  # x
        np.testing.assert_array_almost_equal(result.points[1], [2.0, 5.0, 8.0])  # y
        np.testing.assert_array_almost_equal(result.points[2], [3.0, 6.0, 9.0])  # z
        np.testing.assert_array_almost_equal(result.points[3], [0.5, 0.8, 1.0])  # intensity

    def test_missing_intensity_fills_zeros(self) -> None:
        points = np.array(
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            dtype=np.float32,
        )
        msg = _build_pointcloud2(points, field_names=["x", "y", "z"])

        result = pointcloud2_to_lidar(msg)

        assert result.points.shape == (4, 2)
        np.testing.assert_array_almost_equal(result.points[3], [0.0, 0.0])

    def test_missing_xyz_raises(self) -> None:
        points = np.array([[1.0, 2.0]], dtype=np.float32)
        msg = _build_pointcloud2(points, field_names=["x", "y"])

        with pytest.raises(ValueError, match="missing required field: z"):
            pointcloud2_to_lidar(msg)

    def test_extra_fields_ignored(self) -> None:
        points = np.array(
            [[1.0, 2.0, 3.0, 0.5, 10.0, 20.0]],
            dtype=np.float32,
        )
        msg = _build_pointcloud2(
            points, field_names=["x", "y", "z", "intensity", "ring", "timestamp"]
        )

        result = pointcloud2_to_lidar(msg)

        assert result.points.shape == (4, 1)
        np.testing.assert_array_almost_equal(result.points[:, 0], [1.0, 2.0, 3.0, 0.5])

    def test_empty_pointcloud(self) -> None:
        points = np.zeros((0, 4), dtype=np.float32)
        msg = _build_pointcloud2(points)

        result = pointcloud2_to_lidar(msg)

        assert result.points.shape == (4, 0)

    def test_uint8_intensity(self) -> None:
        """Test with intensity as UINT8 (common in some LiDAR drivers)."""
        n_points = 3
        # Build manually: x(f32), y(f32), z(f32), intensity(u8), padding(3 bytes)
        point_step = 16  # 4+4+4+1+3 padding to align
        fields = [
            MockPointField(name="x", offset=0, datatype=MockPointField.FLOAT32),
            MockPointField(name="y", offset=4, datatype=MockPointField.FLOAT32),
            MockPointField(name="z", offset=8, datatype=MockPointField.FLOAT32),
            MockPointField(name="intensity", offset=12, datatype=MockPointField.UINT8),
        ]

        data = bytearray()
        xyz_values = [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0), (7.0, 8.0, 9.0)]
        intensities = [100, 200, 50]
        for (x, y, z), intensity in zip(xyz_values, intensities):
            data.extend(np.float32(x).tobytes())
            data.extend(np.float32(y).tobytes())
            data.extend(np.float32(z).tobytes())
            data.extend(np.uint8(intensity).tobytes())
            data.extend(b"\x00" * 3)  # padding

        msg = MockPointCloud2(
            height=1,
            width=n_points,
            fields=fields,
            is_bigendian=False,
            point_step=point_step,
            row_step=point_step * n_points,
            data=bytes(data),
        )

        result = pointcloud2_to_lidar(msg)

        assert result.points.shape == (4, 3)
        np.testing.assert_array_almost_equal(result.points[3], [100.0, 200.0, 50.0])
