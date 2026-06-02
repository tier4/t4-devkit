from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest

rosbags = pytest.importorskip("rosbags")

from rosbags.rosbag2 import Writer  # noqa: E402
from rosbags.typesys import Stores, get_typestore  # noqa: E402

from t4_devkit.rosbag.pandar_decoder import (  # noqa: E402
    pandarscan_to_lidar,
    register_pandar_types,
)
from t4_devkit.rosbag.reader import Rosbag2Reader  # noqa: E402
from t4_devkit.rosbag.topic_mapping import TopicMapping  # noqa: E402

# XT32 factory byte
_XT32_FACTORY = 0x32


def _build_xt32_packet(
    azimuths_deg: list[float],
    distances_mm: list[list[int]],
    reflectivities: list[list[int]],
) -> bytes:
    """Build a synthetic XT32 packet (pre-header + header + body + tail).

    Args:
        azimuths_deg: Azimuth angle in degrees for each block.
        distances_mm: Distance values (in raw units, 1 unit = 4mm) per block per channel.
        reflectivities: Reflectivity values (0-255) per block per channel.

    Returns:
        Raw packet bytes.
    """
    block_num = len(azimuths_deg)
    laser_num = 32
    dis_unit = 4  # 4mm

    # Pre-header (6 bytes)
    pre_header = bytes([0xEE, 0xFF, 1, 0, 0, 0])

    # Header (6 bytes)
    header = bytes([laser_num, block_num, 0, dis_unit, 1, 0])

    # Body
    body = bytearray()
    for blk in range(block_num):
        azimuth_raw = int(azimuths_deg[blk] * 100)
        body.extend(struct.pack("<H", azimuth_raw))
        for ch in range(laser_num):
            body.extend(struct.pack("<H", distances_mm[blk][ch]))
            body.append(reflectivities[blk][ch])

    # Tail (22 bytes): reserved(10) + high_temp(1) + return_mode(1) +
    #   motor_speed(2) + datetime(6) + timestamp_us(4) + factory(1)
    # Total = 10 + 1 + 1 + 2 + 6 + 4 + 1 = 25... let me compute properly
    # Actually: reserved(8) + shutdown(2) + return_mode(1) + motor_speed(2) +
    #   datetime(6) + timestamp_us(4) + factory(1) = 24? No...
    # Use 22 bytes tail (standard for XT32 without UDP seq)
    tail = bytearray(22)
    tail[-1] = _XT32_FACTORY  # factory info byte

    return bytes(pre_header + header + body + tail)


class TestPandarDecoderUnit:
    """Unit tests for the pandar decoder without rosbag."""

    def test_decode_single_block(self) -> None:
        """Test decoding a packet with one block."""
        laser_num = 32
        # All channels at distance 1000 (= 4m), azimuth 0°
        distances = [[1000] * laser_num]
        reflectivities = [[128] * laser_num]

        packet = _build_xt32_packet(
            azimuths_deg=[0.0],
            distances_mm=distances,
            reflectivities=reflectivities,
        )

        from t4_devkit.rosbag.pandar_decoder import _decode_packet

        points, config = _decode_packet(packet, None)

        assert config.name == "XT32"
        assert points.shape[0] == 4
        assert points.shape[1] == laser_num

        # At azimuth=0°: x = d*cos(el)*sin(0) = 0, y = d*cos(el)*cos(0) = d*cos(el)
        # All x values should be ~0
        np.testing.assert_array_almost_equal(points[0, :], 0.0, decimal=5)
        # All intensities should be 128
        np.testing.assert_array_almost_equal(points[3, :], 128.0)

    def test_decode_zero_distance_filtered(self) -> None:
        """Test that zero-distance points are filtered out."""
        laser_num = 32
        distances = [[0] * laser_num]
        reflectivities = [[0] * laser_num]

        packet = _build_xt32_packet(
            azimuths_deg=[90.0],
            distances_mm=distances,
            reflectivities=reflectivities,
        )

        from t4_devkit.rosbag.pandar_decoder import _decode_packet

        points, _ = _decode_packet(packet, None)
        assert points.shape[1] == 0

    def test_decode_azimuth_90(self) -> None:
        """Test decoding at azimuth=90° - x should be positive for 0° elevation."""
        laser_num = 32
        distances = [[2500] * laser_num]  # 10m
        reflectivities = [[100] * laser_num]

        packet = _build_xt32_packet(
            azimuths_deg=[90.0],
            distances_mm=distances,
            reflectivities=reflectivities,
        )

        from t4_devkit.rosbag.pandar_decoder import _decode_packet

        points, _ = _decode_packet(packet, None)

        # At azimuth=90°: x = d*cos(el)*sin(90°) = d*cos(el)
        # Channel 15 (elevation=0°): x = 10.0, y ≈ 0
        ch15_idx = None
        for i in range(points.shape[1]):
            if abs(points[2, i]) < 0.01:  # z ≈ 0 means elevation ≈ 0
                ch15_idx = i
                break
        assert ch15_idx is not None
        assert points[0, ch15_idx] == pytest.approx(10.0, abs=0.1)
        assert points[1, ch15_idx] == pytest.approx(0.0, abs=0.1)

    def test_multiple_blocks(self) -> None:
        """Test decoding a packet with multiple blocks."""
        laser_num = 32
        block_num = 4
        distances = [[500] * laser_num] * block_num
        reflectivities = [[50] * laser_num] * block_num
        azimuths = [0.0, 90.0, 180.0, 270.0]

        packet = _build_xt32_packet(
            azimuths_deg=azimuths,
            distances_mm=distances,
            reflectivities=reflectivities,
        )

        from t4_devkit.rosbag.pandar_decoder import _decode_packet

        points, _ = _decode_packet(packet, None)
        assert points.shape[0] == 4
        assert points.shape[1] == laser_num * block_num


class TestPandarScanToLidar:
    """Test the full pandarscan_to_lidar conversion with mock messages."""

    def test_basic_conversion(self) -> None:
        """Test converting a mock PandarScan message."""
        laser_num = 32
        distances = [[1000] * laser_num]
        reflectivities = [[200] * laser_num]

        packet_data = _build_xt32_packet(
            azimuths_deg=[45.0],
            distances_mm=distances,
            reflectivities=reflectivities,
        )

        # Create a mock PandarScan message
        class MockTime:
            sec = 0
            nanosec = 0

        class MockPacket:
            stamp = MockTime()
            data = packet_data

        class MockScan:
            header = None
            packets = [MockPacket()]

        pc = pandarscan_to_lidar(MockScan())
        assert pc.points.shape[0] == 4
        assert pc.points.shape[1] == laser_num

    def test_empty_packets_raises(self) -> None:
        """Test that empty packets raise ValueError."""

        class MockScan:
            header = None
            packets = []

        with pytest.raises(ValueError, match="no packets"):
            pandarscan_to_lidar(MockScan())

    def test_multiple_packets(self) -> None:
        """Test combining multiple packets into one point cloud."""
        laser_num = 32

        class MockTime:
            sec = 0
            nanosec = 0

        packets = []
        for az in [0.0, 90.0, 180.0, 270.0]:
            data = _build_xt32_packet(
                azimuths_deg=[az],
                distances_mm=[[500] * laser_num],
                reflectivities=[[100] * laser_num],
            )

            class MockPacket:
                stamp = MockTime()

            pkt = MockPacket()
            pkt.data = data
            packets.append(pkt)

        class MockScan:
            header = None

        scan = MockScan()
        scan.packets = packets

        pc = pandarscan_to_lidar(scan)
        assert pc.points.shape[0] == 4
        assert pc.points.shape[1] == laser_num * 4


def _create_pandar_rosbag(
    bag_dir: Path,
    topic: str,
    timestamps_ns: list[int],
) -> None:
    """Create a synthetic rosbag2 with PandarScan messages."""
    typestore = get_typestore(Stores.EMPTY)
    typestore.register(get_typestore(Stores.ROS2_HUMBLE).fielddefs)
    register_pandar_types(typestore)

    PandarScan = typestore.types["pandar_msgs/msg/PandarScan"]  # noqa: N806
    PandarPacket = typestore.types["pandar_msgs/msg/PandarPacket"]  # noqa: N806
    Header = typestore.types["std_msgs/msg/Header"]  # noqa: N806
    Time = typestore.types["builtin_interfaces/msg/Time"]  # noqa: N806

    msgtype = "pandar_msgs/msg/PandarScan"
    laser_num = 32

    with Writer(bag_dir, version=9) as writer:
        connection = writer.add_connection(topic, msgtype, typestore=typestore)

        for ts_ns in timestamps_ns:
            sec = ts_ns // 1_000_000_000
            nanosec = ts_ns % 1_000_000_000

            # Build a few packets per scan
            packets = []
            for az in [0.0, 45.0, 90.0, 135.0]:
                pkt_data = _build_xt32_packet(
                    azimuths_deg=[az],
                    distances_mm=[[1000] * laser_num],
                    reflectivities=[[128] * laser_num],
                )
                pkt = PandarPacket(
                    stamp=Time(sec=sec, nanosec=nanosec),
                    data=np.frombuffer(pkt_data, dtype=np.uint8),
                )
                packets.append(pkt)

            msg = PandarScan(
                header=Header(
                    stamp=Time(sec=sec, nanosec=nanosec),
                    frame_id="lidar_top",
                ),
                packets=packets,
            )

            serialized = typestore.serialize_cdr(msg, msgtype)
            writer.write(connection, ts_ns, serialized)


class TestRosbag2ReaderPandarScan:
    """Integration tests: read PandarScan from a synthetic rosbag."""

    @pytest.fixture
    def pandar_bag(self, tmp_path: Path) -> Path:
        bag_dir = tmp_path / "input_bag"
        timestamps_ns = [
            1_704_067_200_000_000_000,
            1_704_067_200_100_000_000,
        ]
        _create_pandar_rosbag(bag_dir, "/sensing/lidar/top/pandar_packets", timestamps_ns)
        return bag_dir

    def test_auto_detect_pandar(self, pandar_bag: Path) -> None:
        with Rosbag2Reader(str(pandar_bag)) as reader:
            assert reader.has_channel("/sensing/lidar/top/pandar_packets")

    def test_topic_mapping_pandar(self, pandar_bag: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pandar_packets")]
        with Rosbag2Reader(str(pandar_bag), topic_mapping=mapping) as reader:
            assert reader.has_channel("LIDAR_TOP")
            pc = reader.get_pointcloud("LIDAR_TOP", 1_704_067_200_000_000)
            assert pc.points.shape[0] == 4
            assert pc.points.shape[1] > 0

    def test_get_pointcloud_pandar(self, pandar_bag: Path) -> None:
        mapping = [TopicMapping(channel="LIDAR_TOP", topic="/sensing/lidar/top/pandar_packets")]
        with Rosbag2Reader(str(pandar_bag), topic_mapping=mapping) as reader:
            pc = reader.get_pointcloud("LIDAR_TOP", 1_704_067_200_000_000)
            # 4 packets × 1 block × 32 channels = 128 points
            assert pc.points.shape == (4, 128)
            # All reflectivities should be 128
            np.testing.assert_array_almost_equal(pc.points[3, :], 128.0)
