from __future__ import annotations

import bisect
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

from t4_devkit.rosbag.pandar_decoder import pandarscan_to_lidar, register_pandar_types
from t4_devkit.rosbag.pointcloud2 import pointcloud2_to_lidar
from t4_devkit.rosbag.topic_mapping import TopicMapping

if TYPE_CHECKING:
    from rosbags.interfaces import Connection

    from t4_devkit.dataclass import LidarPointCloud

__all__ = ["Rosbag2Reader"]

_POINTCLOUD2_MSGTYPE = "sensor_msgs/msg/PointCloud2"
_PANDARSCAN_MSGTYPE = "pandar_msgs/msg/PandarScan"

_SUPPORTED_MSGTYPES = {_POINTCLOUD2_MSGTYPE, _PANDARSCAN_MSGTYPE}

logger = logging.getLogger(__name__)


class Rosbag2Reader:
    """Reader for rosbag2 files that provides LiDAR point cloud data.

    Reads db3 or mcap format rosbag2 files from the ``input_bag/`` directory
    and provides access to LiDAR point cloud data indexed by timestamp.

    Supports both ``sensor_msgs/msg/PointCloud2`` and
    ``pandar_msgs/msg/PandarScan`` (Hesai raw packet) topics.

    Args:
        bag_dir: Path to the rosbag2 directory (containing metadata.yaml).
        topic_mapping: Optional list of ``TopicMapping`` instances.
            If ``None``, supported LiDAR topics are auto-detected from the bag.
    """

    def __init__(
        self,
        bag_dir: str,
        topic_mapping: list[TopicMapping] | None = None,
    ) -> None:
        bag_path = Path(bag_dir)
        if not bag_path.is_dir():
            raise FileNotFoundError(f"Rosbag directory not found: {bag_dir}")

        self._typestore = get_typestore(Stores.EMPTY)
        self._typestore.register(get_typestore(Stores.ROS2_HUMBLE).fielddefs)

        self._reader = Reader(bag_path)
        self._reader.open()
        self._lock = threading.Lock()

        # Find all supported LiDAR connections
        lidar_connections: list[Connection] = [
            conn for conn in self._reader.connections if conn.msgtype in _SUPPORTED_MSGTYPES
        ]

        if not lidar_connections:
            self._reader.close()
            raise ValueError(
                f"No supported LiDAR topics found in rosbag at {bag_dir}. "
                f"Supported types: {_SUPPORTED_MSGTYPES}. "
                f"Available topics: {[c.topic for c in self._reader.connections]}"
            )

        # Register pandar_msgs types if any PandarScan connections exist
        has_pandar = any(c.msgtype == _PANDARSCAN_MSGTYPE for c in lidar_connections)
        if has_pandar:
            register_pandar_types(self._typestore)

        # Build topic <-> channel mapping
        if topic_mapping is not None:
            self._channel_to_topic = TopicMapping.to_channel_dict(topic_mapping)
        else:
            self._channel_to_topic = {conn.topic: conn.topic for conn in lidar_connections}

        topic_to_channel = {v: k for k, v in self._channel_to_topic.items()}

        # Filter connections to only the mapped topics
        mapped_topics = set(self._channel_to_topic.values())
        self._connections = [conn for conn in lidar_connections if conn.topic in mapped_topics]

        # Build timestamp index: channel -> sorted list of timestamp_ns
        # Also build a cached list of timestamp_us per channel for bisect lookups
        self._timestamp_ns: dict[str, list[int]] = {}
        self._timestamp_us: dict[str, list[int]] = {}
        self._build_timestamp_index(topic_to_channel)

        # Warn about mapped channels that have 0 messages
        for channel, topic in self._channel_to_topic.items():
            if channel not in self._timestamp_ns:
                logger.warning(
                    "Topic '%s' (channel '%s') has 0 messages in the rosbag. "
                    "LiDAR data will not be available for this channel.",
                    topic,
                    channel,
                )

    def _build_timestamp_index(self, topic_to_channel: dict[str, str]) -> None:
        """Build timestamp index from the rosbag."""
        raw_index: dict[str, list[tuple[int, int]]] = {}  # channel -> [(ts_us, ts_ns)]

        for conn, timestamp_ns, _rawdata in self._reader.messages(self._connections):
            channel = topic_to_channel[conn.topic]
            if channel not in raw_index:
                raw_index[channel] = []
            raw_index[channel].append((timestamp_ns // 1_000, timestamp_ns))

        for channel, entries in raw_index.items():
            entries.sort()
            self._timestamp_us[channel] = [t[0] for t in entries]
            self._timestamp_ns[channel] = [t[1] for t in entries]

    @property
    def channels(self) -> list[str]:
        """Return list of available channel names."""
        return list(self._timestamp_ns.keys())

    def has_channel(self, channel: str) -> bool:
        """Check if the given channel has indexed messages.

        Args:
            channel: Sensor channel name.

        Returns:
            ``True`` if the channel has indexed messages.
        """
        return channel in self._timestamp_ns

    def get_pointcloud(
        self,
        channel: str,
        timestamp_us: int,
        tolerance_us: int = 75_000,
    ) -> LidarPointCloud:
        """Retrieve a LiDAR point cloud from the rosbag matching the given timestamp.

        Automatically dispatches to the correct decoder based on the topic's
        message type (PointCloud2 or PandarScan).

        Args:
            channel: Sensor channel name.
            timestamp_us: Target timestamp in microseconds (T4 format).
            tolerance_us: Maximum allowed time difference in microseconds.

        Returns:
            LidarPointCloud with shape ``(4, N)`` matching ``LidarPointCloud.from_file`` format.

        Raises:
            KeyError: If the channel is not available.
            ValueError: If no message is found within the tolerance.
        """
        if channel not in self._timestamp_us:
            raise KeyError(f"Channel '{channel}' not found. Available: {self.channels}")

        ts_us_list = self._timestamp_us[channel]
        ts_ns_list = self._timestamp_ns[channel]

        pos = bisect.bisect_left(ts_us_list, timestamp_us)

        # Find the closest timestamp (check pos and pos-1)
        best_idx = None
        best_diff = float("inf")
        for candidate in (pos - 1, pos):
            if 0 <= candidate < len(ts_us_list):
                diff = abs(ts_us_list[candidate] - timestamp_us)
                if diff < best_diff:
                    best_diff = diff
                    best_idx = candidate

        if best_idx is None or best_diff > tolerance_us:
            raise ValueError(
                f"No message found for channel '{channel}' within {tolerance_us}us "
                f"of timestamp {timestamp_us}. "
                f"Closest: {ts_us_list[best_idx] if best_idx is not None else 'N/A'}"
            )

        target_ns = ts_ns_list[best_idx]
        topic = self._channel_to_topic[channel]

        conns_for_topic = [c for c in self._connections if c.topic == topic]
        if not conns_for_topic:
            raise ValueError(f"No connections found for topic '{topic}' (channel '{channel}')")

        with self._lock:
            for conn, ts_ns, rawdata in self._reader.messages(
                connections=conns_for_topic,
                start=target_ns,
                stop=target_ns + 1,
            ):
                msg = self._typestore.deserialize_cdr(rawdata, conn.msgtype)
                if conn.msgtype == _PANDARSCAN_MSGTYPE:
                    return pandarscan_to_lidar(msg)
                return pointcloud2_to_lidar(msg)

        raise ValueError(
            f"Failed to read message for channel '{channel}' at timestamp {target_ns}ns"
        )

    def close(self) -> None:
        """Close the rosbag reader."""
        self._reader.close()

    def __enter__(self) -> Rosbag2Reader:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
