"""Decoder for Hesai PandarScan messages to LidarPointCloud.

Supports decoding raw Hesai LiDAR UDP packets from ``pandar_msgs/msg/PandarScan``
messages into t4-devkit ``LidarPointCloud`` format.

Supported models:
- PandarXT-32 (``XT32``)
- OT128 (``OT128``)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

import numpy as np
from rosbags.interfaces import Nodetype

from t4_devkit.dataclass import LidarPointCloud

__all__ = ["HESAI_MODELS", "pandarscan_to_lidar", "register_pandar_types"]

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
    cos_el: np.ndarray = field(init=False, repr=False, compare=False)
    sin_el: np.ndarray = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        el_rad = np.radians(np.array(self.elevation_deg, dtype=np.float32))
        object.__setattr__(self, "cos_el", np.cos(el_rad))
        object.__setattr__(self, "sin_el", np.sin(el_rad))


# XT32: 32 channels, 1° spacing from +15° to -16°
# https://www.hesaitech.com/product/xt16-32-32m/
_XT32_ELEVATION_DEG: list[float] = [float(15 - i) for i in range(32)]

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
# fmt: on

# Model lookup by sensor type name.
HESAI_MODELS: dict[str, _HesaiModelConfig] = {
    "XT32": _HesaiModelConfig(name="XT32", elevation_deg=_XT32_ELEVATION_DEG),
    "OT128": _HesaiModelConfig(name="OT128", elevation_deg=_OT128_ELEVATION_DEG),
}


def register_pandar_types(typestore: object) -> None:
    """Register ``pandar_msgs`` message types with a rosbags typestore.

    Args:
        typestore: A rosbags ``Typestore`` instance.
    """
    typestore.register(PANDAR_FIELDDEFS)


def pandarscan_to_lidar(msg: object, sensor_type: str) -> LidarPointCloud:
    """Convert a deserialized ``PandarScan`` message to ``LidarPointCloud``.

    Decodes all packets in the scan, converts spherical coordinates to
    Cartesian, and returns a ``LidarPointCloud`` with shape ``(4, N)``.

    Args:
        msg: Deserialized ``pandar_msgs/msg/PandarScan`` message.
        sensor_type: Hesai sensor model name (e.g. ``"OT128"``, ``"XT32"``).

    Returns:
        LidarPointCloud instance.

    Raises:
        ValueError: If no packets, unsupported sensor type, or channel count mismatch.
    """
    config = HESAI_MODELS.get(sensor_type)
    if config is None:
        raise ValueError(
            f"Unsupported sensor type '{sensor_type}'. "
            f"Supported types: {sorted(HESAI_MODELS.keys())}"
        )

    if not msg.packets:
        raise ValueError("PandarScan message contains no packets")

    point_arrays: list[np.ndarray] = []

    for packet in msg.packets:
        data = packet.data[: packet.size]
        raw = data.tobytes() if hasattr(data, "tobytes") else bytes(data)
        if len(raw) < 20:
            continue

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

    azimuths_rad = np.radians(azimuths_raw.astype(np.float32) / 100.0)

    # Hesai native frame: x = d*cos(el)*sin(az), y = d*cos(el)*cos(az), z = d*sin(el)
    # The TF tree (hesai_top -> base_link) handles the frame conversion.
    xy_dist = distances * cos_el
    x = xy_dist * np.sin(azimuths_rad[:, np.newaxis])
    y = xy_dist * np.cos(azimuths_rad[:, np.newaxis])
    z = distances * sin_el

    return np.stack([x[valid], y[valid], z[valid], reflectivities[valid]], axis=0)
