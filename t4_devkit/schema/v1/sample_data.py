from __future__ import annotations

from enum import Enum, unique

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty
from t4_devkit.schema.tables.sensor import SensorModality

from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["FileFormat", "SampleData"]


@unique
class FileFormat(str, Enum):
    """File format of sensor data in T4Dataset 1.0.

    Attributes:
        JPG: JPG image, one file per frame (datasets that keep 0.x files).
        PNG: PNG image, one file per frame (datasets that keep 0.x files).
        PCD: PCD point cloud, one file per frame (datasets that keep 0.x files).
        BIN: BIN point cloud, one file per frame (datasets that keep 0.x files).
        PCDBIN: PCD.BIN point cloud, one file per frame (datasets that keep 0.x files).
        AV1_MP4: AV1 video, one file per camera channel.
        PARQUET: Parquet point cloud, one file per LiDAR channel.
    """

    JPG = "jpg"
    PNG = "png"
    PCD = "pcd"
    BIN = "bin"
    PCDBIN = "pcd.bin"
    AV1_MP4 = "av1_mp4"
    PARQUET = "parquet"


@define(slots=False)
@SCHEMAS.register(SchemaName.SAMPLE_DATA)
class SampleData(SchemaBase):
    """`sample_data.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        sample_token (str | None): Foreign key pointing to the sample, or None if not a key frame.
        ego_pose_token (str): Foreign key pointing to the ego pose.
        sensor_token (str): Foreign key pointing to the sensor.
        filename (str | None): Path to the channel file, or to a per-frame file.
        frame_index (int | None): Index of the frame inside the channel file, or None for
            per-frame files.
        fileformat (FileFormat): Format of the file.
        num_points (int | None): Number of points in the frame. LiDAR only.
        timestamp (int): Unix time stamp [us].
        is_key_frame (bool): Whether this is an annotation key frame.
        is_valid (bool): False if the frame has a sensor drop or synchronization failure.
        next (str | None): Foreign key pointing to the next sample data of the same channel.
        prev (str | None): Foreign key pointing to the previous sample data of the same channel.

    Shortcuts (filled by `T4Tables`):
    ---------
        modality (SensorModality | None): Modality of the sensor.
        channel (str | None): Channel of the sensor.
    """

    sample_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    ego_pose_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    sensor_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    filename: str | None = field(validator=validators.optional(validators.instance_of(str)))
    frame_index: int | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(int), validators.ge(0))
        )
    )
    fileformat: FileFormat = field(converter=FileFormat)
    num_points: int | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(int), validators.ge(0))
        )
    )
    timestamp: int = field(validator=validators.instance_of(int))
    is_key_frame: bool = field(validator=validators.instance_of(bool))
    is_valid: bool = field(validator=validators.instance_of(bool))
    next: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    prev: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )

    # shortcuts
    modality: SensorModality | None = field(init=False, default=None)
    channel: str | None = field(init=False, default=None)
