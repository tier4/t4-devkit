from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest

rosbags = pytest.importorskip("rosbags")

from rosbags.rosbag2 import Writer  # noqa: E402
from rosbags.typesys import Stores, get_typestore  # noqa: E402

from t4_devkit.rosbag.reader import Rosbag2Reader  # noqa: E402
from t4_devkit.rosbag.topic_mapping import TopicMapping  # noqa: E402


def _create_test_rosbag(bag_dir: Path, topic: str, timestamps_ns: list[int]) -> None:
    """Create a synthetic rosbag2 with PointCloud2 messages.

    Args:
        bag_dir: Directory to create the bag in.
        topic: Topic name.
        timestamps_ns: List of timestamps in nanoseconds.
    """
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    PointCloud2 = typestore.types["sensor_msgs/msg/PointCloud2"]  # noqa: N806
    PointField = typestore.types["sensor_msgs/msg/PointField"]  # noqa: N806
    Header = typestore.types["std_msgs/msg/Header"]  # noqa: N806
    Time = typestore.types["builtin_interfaces/msg/Time"]  # noqa: N806

    msgtype = "sensor_msgs/msg/PointCloud2"
    connection = None

    with Writer(bag_dir, version=9) as writer:
        connection = writer.add_connection(topic, msgtype, typestore=typestore)

        for ts_ns in timestamps_ns:
            sec = ts_ns // 1_000_000_000
            nanosec = ts_ns % 1_000_000_000

            # Create a simple PointCloud2 with 3 points
            n_points = 3
            point_step = 16  # x(4) + y(4) + z(4) + intensity(4)
            data = bytearray()
            for i in range(n_points):
                data.extend(struct.pack("<f", float(i)))  # x
                data.extend(struct.pack("<f", float(i + 1)))  # y
                data.extend(struct.pack("<f", float(i + 2)))  # z
                data.extend(struct.pack("<f", float(i) * 0.1))  # intensity

            msg = PointCloud2(
                header=Header(
                    stamp=Time(sec=sec, nanosec=nanosec),
                    frame_id="lidar_top",
                ),
                height=1,
                width=n_points,
                fields=[
                    PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
                    PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
                    PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
                    PointField(name="intensity", offset=12, datatype=PointField.FLOAT32, count=1),
                ],
                is_bigendian=False,
                point_step=point_step,
                row_step=point_step * n_points,
                data=np.frombuffer(bytes(data), dtype=np.uint8),
                is_dense=True,
            )

            serialized = typestore.serialize_cdr(msg, msgtype)
            writer.write(connection, ts_ns, serialized)


class TestRosbag2Reader:
    @pytest.fixture
    def bag_with_pointclouds(self, tmp_path: Path) -> Path:
        """Create a temporary rosbag with PointCloud2 messages."""
        bag_dir = tmp_path / "input_bag"
        timestamps_ns = [
            1_704_067_200_000_000_000,  # 2024-01-01T00:00:00.000
            1_704_067_200_100_000_000,  # 2024-01-01T00:00:00.100
            1_704_067_200_200_000_000,  # 2024-01-01T00:00:00.200
        ]
        _create_test_rosbag(bag_dir, "/sensing/lidar/top/pointcloud", timestamps_ns)
        return bag_dir

    def test_init_auto_detect(self, bag_with_pointclouds: Path) -> None:
        reader = Rosbag2Reader(str(bag_with_pointclouds))
        assert len(reader.channels) == 1
        assert reader.has_channel("/sensing/lidar/top/pointcloud")
        reader.close()

    def test_init_with_topic_mapping(self, bag_with_pointclouds: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")]
        reader = Rosbag2Reader(str(bag_with_pointclouds), topic_mapping=mapping)
        assert reader.has_channel("LIDAR_TOP")
        assert not reader.has_channel("/sensing/lidar/top/pointcloud")
        reader.close()

    def test_get_pointcloud_exact(self, bag_with_pointclouds: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")]
        with Rosbag2Reader(str(bag_with_pointclouds), topic_mapping=mapping) as reader:
            pc = reader.get_pointcloud("LIDAR_TOP", 1_704_067_200_000_000)

            assert pc.points.shape == (4, 3)
            # First point: x=0, y=1, z=2, intensity=0
            np.testing.assert_array_almost_equal(pc.points[:, 0], [0.0, 1.0, 2.0, 0.0])

    def test_get_pointcloud_near_match(self, bag_with_pointclouds: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")]
        with Rosbag2Reader(str(bag_with_pointclouds), topic_mapping=mapping) as reader:
            # Slightly off timestamp (1ms difference), within default 75ms tolerance
            pc = reader.get_pointcloud("LIDAR_TOP", 1_704_067_200_001_000)
            assert pc.points.shape == (4, 3)

    def test_get_pointcloud_out_of_tolerance(self, bag_with_pointclouds: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")]
        with Rosbag2Reader(str(bag_with_pointclouds), topic_mapping=mapping) as reader:
            with pytest.raises(ValueError, match="No message found"):
                # Timestamp far from any message (1 second off)
                reader.get_pointcloud("LIDAR_TOP", 1_704_067_201_000_000)

    def test_get_pointcloud_unknown_channel(self, bag_with_pointclouds: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")]
        with Rosbag2Reader(str(bag_with_pointclouds), topic_mapping=mapping) as reader:
            with pytest.raises(KeyError, match="LIDAR_BOTTOM"):
                reader.get_pointcloud("LIDAR_BOTTOM", 1_704_067_200_000_000)

    def test_missing_directory(self) -> None:
        with pytest.raises(FileNotFoundError):
            Rosbag2Reader("/nonexistent/path")

    def test_context_manager(self, bag_with_pointclouds: Path) -> None:
        with Rosbag2Reader(str(bag_with_pointclouds)) as reader:
            assert len(reader.channels) > 0

    def test_get_pointcloud_start_widened(
        self,
        bag_with_pointclouds: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regression: start is widened by 1ns to dodge rosbags MCAP chunk-filter off-by-one."""
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")]
        with Rosbag2Reader(str(bag_with_pointclouds), topic_mapping=mapping) as reader:
            captured_starts: list[int] = []
            original_messages = reader._reader.messages

            def patched_messages(*args, **kwargs):
                if "start" in kwargs:
                    captured_starts.append(kwargs["start"])
                return original_messages(*args, **kwargs)

            monkeypatch.setattr(reader._reader, "messages", patched_messages)

            target_ts_us = 1_704_067_200_000_000
            target_ts_ns = target_ts_us * 1_000
            pc = reader.get_pointcloud("LIDAR_TOP", target_ts_us)

            assert pc.points.shape == (4, 3)
            assert len(captured_starts) == 1
            assert captured_starts[0] == target_ts_ns - 1

    def test_multiple_timestamps(self, bag_with_pointclouds: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pointcloud")]
        with Rosbag2Reader(str(bag_with_pointclouds), topic_mapping=mapping) as reader:
            # Read all three timestamps
            for ts_us in [
                1_704_067_200_000_000,
                1_704_067_200_100_000,
                1_704_067_200_200_000,
            ]:
                pc = reader.get_pointcloud("LIDAR_TOP", ts_us)
                assert pc.points.shape == (4, 3)
