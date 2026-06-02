"""Decoder for Hesai PandarScan messages to LidarPointCloud.

Supports decoding raw Hesai LiDAR UDP packets from ``pandar_msgs/msg/PandarScan``
messages into t4-devkit ``LidarPointCloud`` format.

Supported models (auto-detected from packet header/data):
- PandarXT-32 (XT32)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

import numpy as np
from rosbags.interfaces import Nodetype

from t4_devkit.dataclass import LidarPointCloud

__all__ = ["pandarscan_to_lidar", "register_pandar_types"]

# pandar_msgs type definitions for rosbags typestore registration.
PANDAR_FIELDDEFS: dict = {
    "pandar_msgs/msg/PandarPacket": (
        [],
        [
            ("stamp", (Nodetype.NAME, "builtin_interfaces/msg/Time")),
            ("data", (Nodetype.SEQUENCE, ((Nodetype.BASE, ("uint8", 0)), 0))),
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
_HEADER_UDP_SEQ = 5


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
_XT32_ELEVATION_DEG: list[float] = [float(15 - i) for i in range(32)]

_KNOWN_MODELS: dict[int, _HesaiModelConfig] = {
    0x32: _HesaiModelConfig(name="XT32", elevation_deg=_XT32_ELEVATION_DEG),
    0x42: _HesaiModelConfig(name="XT32M2X", elevation_deg=_XT32_ELEVATION_DEG),
}


def register_pandar_types(typestore: object) -> None:
    """Register ``pandar_msgs`` message types with a rosbags typestore.

    Args:
        typestore: A rosbags ``Typestore`` instance.
    """
    typestore.register(PANDAR_FIELDDEFS)


def pandarscan_to_lidar(msg: object) -> LidarPointCloud:
    """Convert a deserialized ``PandarScan`` message to ``LidarPointCloud``.

    Decodes all packets in the scan, converts spherical coordinates to
    Cartesian, and returns a ``LidarPointCloud`` with shape ``(4, N)``.

    Args:
        msg: Deserialized ``pandar_msgs/msg/PandarScan`` message.

    Returns:
        LidarPointCloud instance.

    Raises:
        ValueError: If no packets or unsupported model.
    """
    if not msg.packets:
        raise ValueError("PandarScan message contains no packets")

    point_arrays: list[np.ndarray] = []
    config: _HesaiModelConfig | None = None

    for packet in msg.packets:
        raw = bytes(packet.data)
        if len(raw) < 20:
            continue

        points, config = _decode_packet(raw, config)
        if points.shape[1] > 0:
            point_arrays.append(points)

    if not point_arrays:
        return LidarPointCloud(points=np.zeros((4, 0), dtype=np.float32))

    combined = np.concatenate(point_arrays, axis=1)
    return LidarPointCloud(points=combined)


def _decode_packet(
    raw: bytes,
    config: _HesaiModelConfig | None,
) -> tuple[np.ndarray, _HesaiModelConfig]:
    """Decode a single Hesai UDP packet.

    Args:
        raw: Raw packet bytes from ``PandarPacket.data``.
        config: Model config from a previous packet, or ``None``.

    Returns:
        Tuple of (points array (4, N), model config).
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
    udp_seq_enabled = raw[header_offset + _HEADER_UDP_SEQ]

    if dis_unit_mm == 0:
        dis_unit_mm = 4  # default 4mm

    # Determine tail size
    tail_size = 22
    if udp_seq_enabled:
        tail_size += 4

    body_size = len(raw) - body_offset - tail_size
    if body_size <= 0 or block_num == 0 or laser_num == 0:
        raise ValueError(
            f"Invalid packet: body_size={body_size}, blocks={block_num}, lasers={laser_num}"
        )

    block_size = body_size // block_num
    azimuth_bytes = 2
    channel_bytes = (block_size - azimuth_bytes) // laser_num

    if channel_bytes not in (3, 4):
        raise ValueError(
            f"Unexpected channel_bytes={channel_bytes} "
            f"(packet_len={len(raw)}, body={body_size}, blocks={block_num}, lasers={laser_num})"
        )

    # Detect model from factory info byte
    if config is None:
        factory_offset = len(raw) - (4 if udp_seq_enabled else 0) - 1
        factory_byte = raw[factory_offset]
        config = _KNOWN_MODELS.get(factory_byte)
        if config is None:
            config = _HesaiModelConfig(
                name=f"Unknown(0x{factory_byte:02X})",
                elevation_deg=[float(laser_num // 2 - i) for i in range(laser_num)],
            )

    cos_el = config.cos_el[:laser_num]
    sin_el = config.sin_el[:laser_num]

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
        ch_start = blk_start + azimuth_bytes
        ch_end = ch_start + laser_num * channel_bytes
        all_channels[blk] = np.frombuffer(raw[ch_start:ch_end], dtype=ch_dtype)

    # Vectorized conversion across all blocks and channels
    distance_scale = dis_unit_mm / 1000.0
    distances = all_channels["distance"].astype(np.float32) * distance_scale  # (block_num, laser)
    reflectivities = all_channels["reflectivity"].astype(np.float32)

    valid = distances > 0.0
    if not np.any(valid):
        return np.zeros((4, 0), dtype=np.float32), config

    azimuths_rad = np.radians(azimuths_raw.astype(np.float32) / 100.0)  # (block_num,)

    # Broadcast: azimuths (block_num, 1) with trig arrays (laser_num,)
    xy_dist = distances * cos_el  # (block_num, laser_num)
    x = xy_dist * np.sin(azimuths_rad[:, np.newaxis])
    y = xy_dist * np.cos(azimuths_rad[:, np.newaxis])
    z = distances * sin_el

    points = np.stack([x[valid], y[valid], z[valid], reflectivities[valid]], axis=0)
    return points, config
