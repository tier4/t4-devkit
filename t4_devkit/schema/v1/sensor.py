from __future__ import annotations

from enum import Enum, unique
from typing import Any

from attrs import define, field, validators

from t4_devkit.common.converter import to_quaternion
from t4_devkit.schema.tables.base import SchemaBase
from t4_devkit.schema.tables.sensor import SensorModality
from t4_devkit.typing import CameraDistortion, CameraIntrinsic, Quaternion, Vector3

from .name import SchemaName
from .registry import SCHEMAS

__all__ = [
    "DistortionModel",
    "VideoFormat",
    "Video",
    "Camera",
    "LidarContainerFormat",
    "LidarContainer",
    "LidarField",
    "Lidar",
    "Hardware",
    "Sensor",
]


@unique
class DistortionModel(str, Enum):
    """Camera distortion models, as named in ROS CameraInfo."""

    PLUMB_BOB = "plumb_bob"
    RATIONAL_POLYNOMIAL = "rational_polynomial"
    EQUIDISTANT = "equidistant"
    NONE = "none"

    @property
    def num_coefficients(self) -> int:
        """Number of distortion coefficients of this model."""
        return {"plumb_bob": 5, "rational_polynomial": 8, "equidistant": 4, "none": 0}[self.value]


@unique
class VideoFormat(str, Enum):
    """Container and codec of a camera video."""

    AV1_MP4 = "av1_mp4"


@define
class Video:
    """How a camera channel's video is encoded.

    Attributes:
        path (str): Path to the video file, relative to the dataset root.
        format (VideoFormat): Container and codec.
        codec_profile (str): Encoder settings, e.g. "svt-av1 preset6 crf26 intra".
        pixel_format (str): Pixel format, e.g. "yuv420p full-range bt601".
        bit_depth (int): Bits per channel, 8 or 10.
        frame_count (int): Number of frames in the file.
        timescale (int): MP4 track timescale, equal to the frame rate so pts == frame_index.
    """

    path: str = field(validator=validators.instance_of(str))
    format: VideoFormat = field(converter=VideoFormat)
    codec_profile: str = field(validator=validators.instance_of(str))
    pixel_format: str = field(validator=validators.instance_of(str))
    bit_depth: int = field(validator=validators.in_((8, 10)))
    frame_count: int = field(validator=(validators.instance_of(int), validators.ge(0)))
    timescale: int = field(validator=(validators.instance_of(int), validators.ge(1)))


@define
class Camera:
    """Camera sensor.

    Attributes:
        width (int): Image width in pixels.
        height (int): Image height in pixels.
        intrinsic (CameraIntrinsic): 3x3 camera matrix.
        distortion (CameraDistortion): Distortion coefficients, following `distortion_model`.
        distortion_model (DistortionModel): Distortion model.
        is_rectified (bool): Whether the stored images are already rectified.
        video (Video | None): How the video is encoded, or None for per-frame image files.
    """

    width: int = field(validator=(validators.instance_of(int), validators.ge(1)))
    height: int = field(validator=(validators.instance_of(int), validators.ge(1)))
    intrinsic: CameraIntrinsic = field(converter=CameraIntrinsic)
    distortion: CameraDistortion = field(converter=CameraDistortion)
    distortion_model: DistortionModel = field(converter=DistortionModel)
    is_rectified: bool = field(validator=validators.instance_of(bool))
    video: Video | None = field(
        converter=lambda x: Video(**x) if isinstance(x, dict) else x,
        validator=validators.optional(validators.instance_of(Video)),
    )

    @intrinsic.validator
    def _check_intrinsic(self, attribute, value: CameraIntrinsic) -> None:
        if value.shape != (3, 3):
            raise ValueError(
                f"intrinsic must be a 3x3 matrix and cannot be empty for a camera, "
                f"got shape {value.shape}"
            )

    @distortion_model.validator
    def _check_distortion_model(self, attribute, value: DistortionModel) -> None:
        if len(self.distortion) != value.num_coefficients:
            raise ValueError(
                f"distortion_model {value.value!r} has {value.num_coefficients} coefficients, "
                f"got {len(self.distortion)}"
            )


@unique
class LidarContainerFormat(str, Enum):
    """File format of a LiDAR channel."""

    PARQUET = "parquet"
    PCD = "pcd"
    BIN = "bin"


@define
class LidarContainer:
    """How a LiDAR channel's points are stored.

    Attributes:
        format (LidarContainerFormat): File format.
        path (str | None): Path to the file, or None for per-frame files.
        frame_count (int): Number of frames.
        compression (str): Compression profile, e.g. "zstd", or "none".
    """

    format: LidarContainerFormat = field(converter=LidarContainerFormat)
    path: str | None = field(validator=validators.optional(validators.instance_of(str)))
    frame_count: int = field(validator=(validators.instance_of(int), validators.ge(0)))
    compression: str = field(validator=validators.instance_of(str))


@define
class LidarField:
    """A point field of a LiDAR channel.

    Attributes:
        name (str): Field name, e.g. "x".
        dtype (str): Data type, e.g. "float32".
    """

    name: str = field(validator=validators.instance_of(str))
    dtype: str = field(validator=validators.instance_of(str))


@define
class Lidar:
    """LiDAR block of a sensor.

    Attributes:
        container (LidarContainer): How the points are stored.
        fields (list[LidarField]): Point fields in column order.
        source_channels (list[str]): LiDAR channels merged into this one; empty if none.
        frame_id (str): Coordinate frame of the stored points.
        is_undistorted (bool): Whether points are motion and scan compensated.
    """

    container: LidarContainer = field(
        converter=lambda x: LidarContainer(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(LidarContainer),
    )
    fields: list[LidarField] = field(
        converter=lambda x: [LidarField(**v) if isinstance(v, dict) else v for v in x],
        validator=validators.deep_iterable(
            validators.instance_of(LidarField), validators.instance_of(list)
        ),
    )
    source_channels: list[str] = field(
        validator=validators.deep_iterable(
            validators.instance_of(str), validators.instance_of(list)
        )
    )
    frame_id: str = field(validator=validators.instance_of(str))
    is_undistorted: bool = field(validator=validators.instance_of(bool))


@define
class Hardware:
    """Sensor hardware identity.

    Attributes:
        make (str | None): Manufacturer.
        model (str | None): Model.
        serial_number (str | None): Serial number.
        firmware_version (str | None): Firmware version.
    """

    make: str | None = field(validator=validators.optional(validators.instance_of(str)))
    model: str | None = field(validator=validators.optional(validators.instance_of(str)))
    serial_number: str | None = field(validator=validators.optional(validators.instance_of(str)))
    firmware_version: str | None = field(validator=validators.optional(validators.instance_of(str)))


@define(slots=False)
@SCHEMAS.register(SchemaName.SENSOR)
class Sensor(SchemaBase):
    """`sensor.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        channel (str): Sensor channel name.
        index (int): Sensor index, unique within the dataset; value of the LiDAR `source_index`
            field for points from this sensor.
        modality (SensorModality): Sensor modality.
        translation (Vector3): Sensor position relative to base_link [m].
        rotation (Quaternion): Sensor orientation relative to base_link, as [w, x, y, z].
        camera (Camera | None): Camera block, set when modality is camera.
        lidar (Lidar | None): LiDAR block, set when modality is lidar.
        radar (dict[str, Any] | None): Radar block, not defined in 1.0.
        hardware (Hardware | None): Sensor hardware identity.

    Shortcuts (filled by `T4Tables`):
    ---------
        first_sd_token (str | None): Token of the earliest sample data of this sensor.
    """

    channel: str = field(validator=validators.instance_of(str))
    index: int = field(
        validator=(validators.instance_of(int), validators.ge(0), validators.le(255))
    )
    modality: SensorModality = field(converter=SensorModality)
    translation: Vector3 = field(converter=Vector3)
    rotation: Quaternion = field(converter=to_quaternion)
    camera: Camera | None = field(
        converter=lambda x: Camera(**x) if isinstance(x, dict) else x,
        validator=validators.optional(validators.instance_of(Camera)),
    )
    lidar: Lidar | None = field(
        converter=lambda x: Lidar(**x) if isinstance(x, dict) else x,
        validator=validators.optional(validators.instance_of(Lidar)),
    )
    radar: dict[str, Any] | None = field(
        validator=validators.optional(validators.instance_of(dict))
    )
    hardware: Hardware | None = field(
        converter=lambda x: Hardware(**x) if isinstance(x, dict) else x,
        validator=validators.optional(validators.instance_of(Hardware)),
    )

    # shortcuts
    first_sd_token: str | None = field(init=False, default=None)

    def __attrs_post_init__(self) -> None:
        """Post-initialization validation: only the block matching `modality` is set."""
        blocks = {
            SensorModality.CAMERA: self.camera,
            SensorModality.LIDAR: self.lidar,
            SensorModality.RADAR: self.radar,
        }
        for modality, block in blocks.items():
            if (block is not None) != (modality == self.modality):
                raise ValueError(
                    f"Sensor {self.channel!r} has modality {self.modality.value!r}: "
                    f"only the {self.modality.value!r} block must be set."
                )
