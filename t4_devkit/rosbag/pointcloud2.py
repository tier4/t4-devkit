from __future__ import annotations

import numpy as np

from t4_devkit.dataclass import LidarPointCloud

__all__ = ["pointcloud2_to_lidar"]

# PointField datatype constants -> numpy dtype mapping
_DATATYPE_TO_NUMPY = {
    1: np.int8,  # INT8
    2: np.uint8,  # UINT8
    3: np.int16,  # INT16
    4: np.uint16,  # UINT16
    5: np.int32,  # INT32
    6: np.uint32,  # UINT32
    7: np.float32,  # FLOAT32
    8: np.float64,  # FLOAT64
}


def pointcloud2_to_lidar(msg: object) -> LidarPointCloud:
    """Convert a deserialized PointCloud2 message to LidarPointCloud.

    Extracts x, y, z, intensity fields from the message and returns
    a LidarPointCloud with shape (4, N), matching the format returned
    by ``LidarPointCloud.from_file``.

    Args:
        msg: Deserialized ``sensor_msgs/msg/PointCloud2`` message.

    Returns:
        LidarPointCloud instance.

    Raises:
        ValueError: If required fields (x, y, z) are not found.
    """
    field_map: dict[str, tuple[int, int]] = {}  # name -> (offset, datatype)
    for f in msg.fields:
        field_map[f.name] = (f.offset, f.datatype)

    for required in ("x", "y", "z"):
        if required not in field_map:
            raise ValueError(f"PointCloud2 message is missing required field: {required}")

    num_points = msg.height * msg.width
    point_step = msg.point_step

    # Build a structured numpy dtype that covers all fields + padding
    sorted_fields = sorted(msg.fields, key=lambda f: f.offset)
    dt_list: list[tuple[str, type, int] | tuple[str, type]] = []
    offset = 0
    for f in sorted_fields:
        if f.offset > offset:
            dt_list.append((f"_pad{offset}", np.void, f.offset - offset))

        np_dtype_base = _DATATYPE_TO_NUMPY.get(f.datatype)
        if np_dtype_base is None:
            raise ValueError(f"Unsupported PointField datatype: {f.datatype} for field '{f.name}'")
        np_dtype = np.dtype(np_dtype_base).newbyteorder(">" if msg.is_bigendian else "<")

        count = int(getattr(f, "count", 1))
        if count < 1:
            raise ValueError(f"Invalid PointField count for field '{f.name}': {count}")

        dt_list.append((f.name, np_dtype) if count == 1 else (f.name, np_dtype, count))
        offset = f.offset + np_dtype.itemsize * count
    if offset < point_step:
        dt_list.append(("_pad_end", np.void, point_step - offset))
    dtype = np.dtype(dt_list)
    structured = np.frombuffer(msg.data, dtype=dtype, count=num_points)

    x = structured["x"].astype(np.float32)
    y = structured["y"].astype(np.float32)
    z = structured["z"].astype(np.float32)
    intensity = (
        structured["intensity"].astype(np.float32)
        if "intensity" in field_map
        else np.zeros(num_points, dtype=np.float32)
    )

    points = np.stack([x, y, z, intensity], axis=0)
    return LidarPointCloud(points=points)
