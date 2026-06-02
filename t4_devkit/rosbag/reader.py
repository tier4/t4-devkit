from __future__ import annotations

import bisect
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

from t4_devkit.rosbag.pandar_decoder import (
    HESAI_MODELS,
    pandarscan_to_lidar,
    register_pandar_types,
)
from t4_devkit.rosbag.pointcloud2 import pointcloud2_to_lidar
from t4_devkit.rosbag.topic_mapping import TopicMapping

if TYPE_CHECKING:
    from rosbags.interfaces import Connection

    from t4_devkit.dataclass import LidarPointCloud

__all__ = ["Rosbag2Reader"]

_POINTCLOUD2_MSGTYPE = "sensor_msgs/msg/PointCloud2"
_PANDARSCAN_MSGTYPE = "pandar_msgs/msg/PandarScan"
_TF_STATIC_TOPIC = "/tf_static"

_SUPPORTED_MSGTYPES = {_POINTCLOUD2_MSGTYPE, _PANDARSCAN_MSGTYPE}

logger = logging.getLogger(__name__)


def _quat_to_matrix(x: float, y: float, z: float, w: float) -> np.ndarray:
    """Convert quaternion (x, y, z, w) to a 3x3 rotation matrix."""
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


def _build_tf_to_base(typestore: object, reader: Reader) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Read /tf_static and compute transforms from each frame to base_link.

    Returns:
        Dict mapping ``frame_id`` to ``(R, t)`` where ``R`` is a 3x3 rotation
        matrix and ``t`` is a 3-element translation vector, representing the
        transform from that frame to ``base_link``.
    """
    tf_conns = [c for c in reader.connections if c.topic == _TF_STATIC_TOPIC]
    if not tf_conns:
        return {}

    # Parse the TF tree: child_frame -> (parent_frame, R, t)
    tree: dict[str, tuple[str, np.ndarray, np.ndarray]] = {}
    for conn, _ts, rawdata in reader.messages(connections=tf_conns):
        msg = typestore.deserialize_cdr(rawdata, conn.msgtype)
        for tf in msg.transforms:
            parent = tf.header.frame_id
            child = tf.child_frame_id
            tr = tf.transform.translation
            rot = tf.transform.rotation
            R = _quat_to_matrix(rot.x, rot.y, rot.z, rot.w)
            t = np.array([tr.x, tr.y, tr.z])
            tree[child] = (parent, R, t)

    # Compose transforms from each frame to base_link
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    result["base_link"] = (np.eye(3), np.zeros(3))

    def _resolve(frame: str) -> tuple[np.ndarray, np.ndarray] | None:
        if frame in result:
            return result[frame]
        if frame not in tree:
            return None
        parent, R_child, t_child = tree[frame]
        parent_tf = _resolve(parent)
        if parent_tf is None:
            return None
        R_parent, t_parent = parent_tf
        # T_base = T_parent * T_child: p_base = R_parent*(R_child*p + t_child) + t_parent
        R = R_parent @ R_child
        t = R_parent @ t_child + t_parent
        result[frame] = (R, t)
        return result[frame]

    for frame in tree:
        _resolve(frame)

    return result


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

        # Build topic <-> channel mapping and sensor_type mapping
        if topic_mapping is not None:
            self._channel_to_topic = TopicMapping.to_channel_dict(topic_mapping)
            self._channel_to_sensor_type: dict[str, str | None] = {
                m.channel: m.sensor_type for m in topic_mapping
            }
        else:
            # Auto-detect mode: only include PointCloud2 topics (PandarScan requires
            # explicit sensor_type via TopicMapping).
            auto_connections = [
                conn for conn in lidar_connections if conn.msgtype != _PANDARSCAN_MSGTYPE
            ]
            self._channel_to_topic = {conn.topic: conn.topic for conn in auto_connections}
            self._channel_to_sensor_type = {}

        # Validate sensor_type for PandarScan topics
        pandar_topics = {c.topic for c in lidar_connections if c.msgtype == _PANDARSCAN_MSGTYPE}
        for channel, topic in self._channel_to_topic.items():
            if topic in pandar_topics:
                sensor_type = self._channel_to_sensor_type.get(channel)
                if sensor_type is None:
                    raise ValueError(
                        f"Topic '{topic}' (channel '{channel}') is a PandarScan topic. "
                        f"sensor_type must be specified in TopicMapping. "
                        f"Supported types: {sorted(HESAI_MODELS.keys())}"
                    )
                if sensor_type not in HESAI_MODELS:
                    raise ValueError(
                        f"Unsupported sensor_type '{sensor_type}' for channel '{channel}'. "
                        f"Supported types: {sorted(HESAI_MODELS.keys())}"
                    )

        topic_to_channel = {v: k for k, v in self._channel_to_topic.items()}

        # Filter connections to only the mapped topics, indexed by topic for O(1) lookup
        mapped_topics = set(self._channel_to_topic.values())
        self._connections = [conn for conn in lidar_connections if conn.topic in mapped_topics]
        self._topic_connections: dict[str, list[Connection]] = {}
        for conn in self._connections:
            self._topic_connections.setdefault(conn.topic, []).append(conn)

        # Read /tf_static and build transforms to base_link
        self._tf_to_base = _build_tf_to_base(self._typestore, self._reader)

        # For PandarScan topics with frame_id specified, look up TF transform
        self._channel_tf: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        if topic_mapping is not None:
            for m in topic_mapping:
                if m.frame_id is None:
                    continue
                if m.frame_id in self._tf_to_base:
                    self._channel_tf[m.channel] = self._tf_to_base[m.frame_id]
                else:
                    logger.warning(
                        "Channel '%s': frame_id='%s' not found in /tf_static. "
                        "Points will be in sensor frame.",
                        m.channel,
                        m.frame_id,
                    )

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
        raw_ns: dict[str, list[int]] = {}

        for conn, timestamp_ns, _rawdata in self._reader.messages(self._connections):
            channel = topic_to_channel[conn.topic]
            raw_ns.setdefault(channel, []).append(timestamp_ns)

        for channel, ns_list in raw_ns.items():
            ns_list.sort()
            self._timestamp_ns[channel] = ns_list
            self._timestamp_us[channel] = [t // 1_000 for t in ns_list]

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

        conns_for_topic = self._topic_connections.get(topic)
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
                    pc = pandarscan_to_lidar(msg, self._channel_to_sensor_type[channel])
                    tf = self._channel_tf.get(channel)
                    if tf is not None:
                        R, t = tf
                        xyz = pc.points[:3, :]
                        pc.points[:3, :] = R @ xyz + t[:, np.newaxis]
                    return pc
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
