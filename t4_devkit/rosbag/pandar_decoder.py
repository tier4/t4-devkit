"""Decoder for Hesai PandarScan messages to LidarPointCloud.

Supports decoding raw Hesai LiDAR UDP packets from ``pandar_msgs/msg/PandarScan``
messages into t4-devkit ``LidarPointCloud`` format.

Supported models:
- PandarXT-32 (``XT32``)
- OT128 (``OT128``)
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass, field

import numpy as np
from rosbags.interfaces import Nodetype

from t4_devkit.dataclass import LidarPointCloud

__all__ = ["HESAI_MODELS", "pandarscan_to_lidar", "register_pandar_types"]

logger = logging.getLogger(__name__)

# pandar_msgs type definitions for rosbags typestore registration.
# PandarPacket uses a fixed uint8[1500] data buffer with a uint32 size field
# indicating the actual number of valid bytes.
_PANDAR_DATA_BUFFER_SIZE = 1500

PANDAR_FIELDDEFS: dict = {
    "pandar_msgs/msg/PandarPacket": (
        [],
        [
            ("stamp", (Nodetype.NAME, "builtin_interfaces/msg/Time")),
            (
                "data",
                (Nodetype.ARRAY, ((Nodetype.BASE, ("uint8", 0)), _PANDAR_DATA_BUFFER_SIZE)),
            ),
            ("size", (Nodetype.BASE, ("uint32", 0))),
        ],
    ),
    "pandar_msgs/msg/PandarScan": (
        [],
        [
            ("header", (Nodetype.NAME, "std_msgs/msg/Header")),
            (
                "packets",
                (Nodetype.SEQUENCE, ((Nodetype.NAME, "pandar_msgs/msg/PandarPacket"), 0)),
            ),
        ],
    ),
}

# Hesai packet magic bytes
_HESAI_SOF = (0xEE, 0xFF)

# Pre-header + header size when SOF is present
_PRE_HEADER_SIZE = 6
_HEADER_SIZE = 6

# Header field offsets (relative to header start, i.e. after pre-header)
_HEADER_LASER_NUM = 0
_HEADER_BLOCK_NUM = 1
_HEADER_DIS_UNIT = 3

_AZIMUTH_BYTES = 2

_EMPTY_POINTS = np.zeros((4, 0), dtype=np.float32)


@dataclass(frozen=True)
class _HesaiModelConfig:
    """Configuration for a Hesai LiDAR model."""

    name: str
    elevation_deg: list[float] = field(repr=False)
    azimuth_offset_deg: list[float] = field(repr=False)
    udp_seq_offset_from_end: int = 4
    """Byte offset from the end of the raw packet to the start of the 4-byte
    UDP Sequence field (u32 LE).  XT32: 4 (last 4 bytes, in "Additional
    information").  OT128: 30 (in Tail, followed by 26 bytes of IMU data)."""
    cos_el: np.ndarray = field(init=False, repr=False, compare=False)
    sin_el: np.ndarray = field(init=False, repr=False, compare=False)
    azimuth_offset_rad: np.ndarray = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        el_rad = np.radians(np.array(self.elevation_deg, dtype=np.float32))
        object.__setattr__(self, "cos_el", np.cos(el_rad))
        object.__setattr__(self, "sin_el", np.sin(el_rad))
        object.__setattr__(
            self,
            "azimuth_offset_rad",
            np.radians(np.array(self.azimuth_offset_deg, dtype=np.float32)),
        )


# XT32: 32 channels, 1° spacing from +15° to -16°
# https://www.hesaitech.com/product/xt16-32-32m/
_XT32_ELEVATION_DEG: list[float] = [float(15 - i) for i in range(32)]
_XT32_AZIMUTH_OFFSET_DEG: list[float] = [0.0] * 32

# OT128: 128 channels, non-uniform spacing from +14.985° to -24.765°
# Per Hesai OT128 User Manual (O01-en-260410), Appendix A / Angle Correction File:
# https://www.hesaitech.com/product/ot128/
# fmt: off
_OT128_ELEVATION_DEG: list[float] = [
    14.985, 13.283, 11.758, 10.483, 9.836, 9.171, 8.496, 7.812,
    7.462, 7.115, 6.767, 6.416, 6.064, 5.71, 5.355, 4.998,
    4.643, 4.282, 3.921, 3.558, 3.194, 2.829, 2.463, 2.095,
    1.974, 1.854, 1.729, 1.609, 1.487, 1.362, 1.242, 1.12,
    0.995, 0.875, 0.75, 0.625, 0.5, 0.375, 0.25, 0.125,
    0.0, -0.125, -0.25, -0.375, -0.5, -0.626, -0.751, -0.876,
    -1.001, -1.126, -1.251, -1.377, -1.502, -1.627, -1.751, -1.876,
    -2.001, -2.126, -2.251, -2.376, -2.501, -2.626, -2.751, -2.876,
    -3.001, -3.126, -3.251, -3.376, -3.501, -3.626, -3.751, -3.876,
    -4.001, -4.126, -4.25, -4.375, -4.501, -4.626, -4.751, -4.876,
    -5.001, -5.126, -5.252, -5.377, -5.502, -5.626, -5.752, -5.877,
    -6.002, -6.378, -6.754, -7.13, -7.507, -7.882, -8.257, -8.632,
    -9.003, -9.376, -9.749, -10.121, -10.493, -10.864, -11.234, -11.603,
    -11.975, -12.343, -12.709, -13.075, -13.439, -13.803, -14.164, -14.525,
    -14.879, -15.237, -15.593, -15.948, -16.299, -16.651, -17.0, -17.347,
    -17.701, -18.386, -19.063, -19.73, -20.376, -21.653, -23.044, -24.765,
]
_OT128_AZIMUTH_OFFSET_DEG: list[float] = [
    0.186, 0.185, 1.335, 1.343, 0.148, 0.147, 0.146, 0.146,
    1.335, 1.336, 1.337, 1.338, 1.339, 1.34, 1.341, 1.342,
    0.128, 0.128, 0.127, 0.127, 0.107, 0.106, 0.105, 0.105,
    -3.118, 1.315, 4.529, -3.121, 1.316, 4.532, -3.124, 1.317,
    4.536, -3.127, 1.317, 4.539, -3.13, 1.318, 4.542, -3.133,
    0.103, 2.935, -1.517, 0.103, 2.937, -1.519, 0.103, 2.939,
    -1.52, 0.103, 2.941, -1.521, 0.102, 2.943, -1.523, 0.102,
    2.945, -1.524, 0.102, 2.946, -1.526, 0.102, 2.948, -1.526,
    1.324, 4.57, -3.155, 1.325, 4.573, -3.157, 1.326, 4.575,
    -3.159, 1.326, 4.578, -3.161, 1.327, 4.581, -3.163, 1.328,
    4.583, -3.165, 1.329, 4.586, -3.167, 1.329, 4.588, -3.168,
    0.102, 0.103, 0.103, 0.103, 0.104, 0.104, 0.104, 0.104,
    1.337, 1.337, 1.338, 1.339, 1.34, 1.341, 1.341, 1.342,
    0.108, 0.108, 0.109, 0.109, 0.13, 0.131, 0.131, 0.132,
    1.384, 1.384, 1.385, 1.385, 1.386, 1.386, 1.387, 1.387,
    0.151, 0.153, 0.154, 0.156, 1.388, 1.408, 0.196, 0.286,
]
# fmt: on

# Model lookup by sensor type name.
HESAI_MODELS: dict[str, _HesaiModelConfig] = {
    "XT32": _HesaiModelConfig(
        name="XT32",
        elevation_deg=_XT32_ELEVATION_DEG,
        azimuth_offset_deg=_XT32_AZIMUTH_OFFSET_DEG,
    ),
    "OT128": _HesaiModelConfig(
        name="OT128",
        elevation_deg=_OT128_ELEVATION_DEG,
        azimuth_offset_deg=_OT128_AZIMUTH_OFFSET_DEG,
        udp_seq_offset_from_end=30,
    ),
}


def register_pandar_types(typestore: object) -> None:
    """Register ``pandar_msgs`` message types with a rosbags typestore.

    Args:
        typestore: A rosbags ``Typestore`` instance.
    """
    typestore.register(PANDAR_FIELDDEFS)


def _extract_udp_sequence(raw: bytes, config: _HesaiModelConfig) -> int | None:
    """Extract the UDP Sequence number from a raw Hesai packet.

    The UDP Sequence is a monotonically incrementing u32 counter embedded
    in each UDP packet.  Its byte offset from the end of the packet varies
    by model (see ``_HesaiModelConfig.udp_seq_offset_from_end``).

    Args:
        raw: Raw packet bytes (trimmed to actual size).
        config: Model config for the sensor type.

    Returns:
        UDP Sequence number (u32), or ``None`` if the packet is too short.
    """
    if len(raw) < config.udp_seq_offset_from_end + 4:
        return None
    offset = len(raw) - config.udp_seq_offset_from_end
    return struct.unpack_from("<I", raw, offset)[0]


def pandarscan_to_lidar(
    msg: object,
    sensor_type: str,
    min_completeness: float = 1.0,
) -> LidarPointCloud:
    """Convert a deserialized ``PandarScan`` message to ``LidarPointCloud``.

    Decodes all packets in the scan, converts spherical coordinates to
    Cartesian, and returns a ``LidarPointCloud`` with shape ``(4, N)``.

    When *min_completeness* > 0, the UDP Sequence numbers embedded in each
    packet are checked.  If the ratio ``actual_packets / expected_packets``
    is below *min_completeness*, a :class:`ValueError` is raised to indicate
    that the scan is incomplete (packets were dropped during recording).

    Args:
        msg: Deserialized ``pandar_msgs/msg/PandarScan`` message.
        sensor_type: Hesai sensor model name (e.g. ``"OT128"``, ``"XT32"``).
        min_completeness: Minimum fraction of expected packets that must be
            present (0.0–1.0).  Defaults to ``1.0`` (reject any scan with
            dropped packets).  Set to ``0.0`` to disable the check.

    Returns:
        LidarPointCloud instance.

    Raises:
        ValueError: If no packets, unsupported sensor type, channel count
            mismatch, or scan completeness is below *min_completeness*.
    """
    config = HESAI_MODELS.get(sensor_type)
    if config is None:
        raise ValueError(
            f"Unsupported sensor type '{sensor_type}'. "
            f"Supported types: {sorted(HESAI_MODELS.keys())}"
        )

    if not msg.packets:
        raise ValueError("PandarScan message contains no packets")

    # Extract raw bytes and UDP sequences for each packet.
    raw_packets: list[bytes] = []
    for packet in msg.packets:
        data = packet.data[: packet.size]
        raw = data.tobytes() if hasattr(data, "tobytes") else bytes(data)
        if len(raw) < 20:
            continue
        raw_packets.append(raw)

    if not raw_packets:
        raise ValueError("PandarScan message contains no valid packets")

    # Check scan completeness via UDP Sequence.
    # Packets in a PandarScan are assembled by the ROS driver in
    # chronological (azimuth) order, so first/last is sufficient.
    if min_completeness > 0.0 and len(raw_packets) >= 2:
        first_seq = _extract_udp_sequence(raw_packets[0], config)
        last_seq = _extract_udp_sequence(raw_packets[-1], config)
        if first_seq is not None and last_seq is not None:
            expected = last_seq - first_seq + 1
            actual = len(raw_packets)
            if expected > 0:
                completeness = actual / expected
                if completeness < min_completeness:
                    raise ValueError(
                        f"Incomplete PandarScan: {actual}/{expected} packets "
                        f"({completeness:.1%} completeness, "
                        f"threshold={min_completeness:.1%}). "
                        f"UDP Sequence range: {first_seq}–{last_seq}."
                    )
                if completeness < 1.0:
                    dropped = expected - actual
                    logger.debug(
                        "PandarScan has %d/%d packets (%.1f%% complete, "
                        "%d dropped). Proceeding (above %.0f%% threshold).",
                        actual,
                        expected,
                        completeness * 100,
                        dropped,
                        min_completeness * 100,
                    )

    point_arrays: list[np.ndarray] = []
    for raw in raw_packets:
        points = _decode_packet(raw, config)
        if points.shape[1] > 0:
            point_arrays.append(points)

    if not point_arrays:
        return LidarPointCloud(points=_EMPTY_POINTS)

    combined = np.concatenate(point_arrays, axis=1)
    return LidarPointCloud(points=combined)


def _decode_packet(
    raw: bytes,
    config: _HesaiModelConfig,
) -> np.ndarray:
    """Decode a single Hesai UDP packet.

    Args:
        raw: Raw packet bytes (trimmed to actual size via ``PandarPacket.size``).
        config: Model config for the sensor type.

    Returns:
        Points array with shape ``(4, N)`` in Hesai native frame
        (x=d*cos*sin, y=d*cos*cos, z=d*sin).

    Raises:
        ValueError: If the packet channel count doesn't match the config.
    """
    has_sof = raw[0] == _HESAI_SOF[0] and raw[1] == _HESAI_SOF[1]

    if has_sof:
        header_offset = _PRE_HEADER_SIZE
        body_offset = _PRE_HEADER_SIZE + _HEADER_SIZE
    else:
        header_offset = 0
        body_offset = _HEADER_SIZE

    laser_num = raw[header_offset + _HEADER_LASER_NUM]
    block_num = raw[header_offset + _HEADER_BLOCK_NUM]
    dis_unit_mm = raw[header_offset + _HEADER_DIS_UNIT]

    if dis_unit_mm == 0:
        dis_unit_mm = 4  # default 4mm

    if block_num == 0 or laser_num == 0:
        raise ValueError(f"Invalid packet header: blocks={block_num}, lasers={laser_num}")

    expected_channels = len(config.elevation_deg)
    if laser_num != expected_channels:
        raise ValueError(
            f"Packet channel count ({laser_num}) does not match "
            f"sensor type '{config.name}' ({expected_channels} channels)"
        )

    # Hesai firmware uses either 3-byte (distance+reflectivity) or 4-byte
    # (distance+reflectivity+reserved) channel layout with no explicit field
    # in the header. Infer by checking which layout leaves a valid tail.
    channel_bytes = 0
    for ch_bytes in (4, 3):
        block_size = _AZIMUTH_BYTES + laser_num * ch_bytes
        body_size = block_num * block_size
        tail = len(raw) - body_offset - body_size
        if tail >= 12:
            channel_bytes = ch_bytes
            break

    if channel_bytes == 0:
        raise ValueError(
            f"Cannot determine channel layout "
            f"(packet_len={len(raw)}, blocks={block_num}, lasers={laser_num})"
        )

    block_size = _AZIMUTH_BYTES + laser_num * channel_bytes

    cos_el = config.cos_el
    sin_el = config.sin_el

    # Build structured dtype for channel data
    if channel_bytes == 3:
        ch_dtype = np.dtype([("distance", "<u2"), ("reflectivity", "u1")])
    else:
        ch_dtype = np.dtype([("distance", "<u2"), ("reflectivity", "u1"), ("_pad", "u1")])

    # Parse all blocks: read azimuths and channel data
    azimuths_raw = np.empty(block_num, dtype=np.uint16)
    all_channels = np.empty((block_num, laser_num), dtype=ch_dtype)

    for blk in range(block_num):
        blk_start = body_offset + blk * block_size
        azimuths_raw[blk] = struct.unpack_from("<H", raw, blk_start)[0]
        ch_start = blk_start + _AZIMUTH_BYTES
        ch_end = ch_start + laser_num * channel_bytes
        all_channels[blk] = np.frombuffer(raw[ch_start:ch_end], dtype=ch_dtype)

    # Vectorized conversion across all blocks and channels
    distance_scale = dis_unit_mm / 1000.0
    distances = all_channels["distance"].astype(np.float32) * distance_scale
    reflectivities = all_channels["reflectivity"].astype(np.float32)

    valid = distances > 0.0
    if not np.any(valid):
        return _EMPTY_POINTS

    # Per-channel azimuth: block azimuth + channel-specific offset
    block_az_rad = np.radians(azimuths_raw.astype(np.float32) / 100.0)
    azimuths_rad = block_az_rad[:, np.newaxis] + config.azimuth_offset_rad

    # Hesai native frame: x = d*cos(el)*sin(az), y = d*cos(el)*cos(az), z = d*sin(el)
    # The TF tree (hesai_top -> base_link) handles the frame conversion.
    xy_dist = distances * cos_el
    x = xy_dist * np.sin(azimuths_rad)
    y = xy_dist * np.cos(azimuths_rad)
    z = distances * sin_el

    return np.stack([x[valid], y[valid], z[valid], reflectivities[valid]], axis=0)
