from __future__ import annotations

from enum import Enum, unique
from typing import TYPE_CHECKING

from attrs import define, field, validators

from ..name import SchemaName
from .autolabel_metadata import AutolabelModel
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from .sensor import SensorModality

__all__ = ["SampleData", "FileFormat"]


@unique
class FileFormat(str, Enum):
    """An enum to represent file formats.

    Attributes:
        JPG: JPG format for image data.
        PNG: PNG format for image data.
        PCD: PCD format for pointcloud data.
        BIN: BIN format.
        PCDBIN: PCD.BIN format for pointcloud data.
    """

    JPG = "jpg"
    PNG = "png"
    PCD = "pcd"
    BIN = "bin"
    PCDBIN = "pcd.bin"

    @staticmethod
    def is_member(item: str) -> bool:
        """Indicate whether the input item is the one of members of FileFormat.

        Args:
            item (str): Any file format name.

        Returns:
            Return True if the item is included.
        """
        return item in FileFormat.values()

    @staticmethod
    def values() -> list[str]:
        """Return a list of values of members.

        Returns:
            List of values.
        """
        return [v.value for v in FileFormat]

    def as_ext(self) -> str:
        """Return the value as file extension.

        Returns:
            File extension.
        """
        return f".{self.value}"


@define(slots=False)
@SCHEMAS.register(SchemaName.SAMPLE_DATA)
class SampleData(SchemaBase):
    """A class to represent schema table of `sample_data.json`.

    Attributes:
        token (str): Unique record identifier.
        sample_token (str): Foreign key pointing the sample.
        ego_pose_token (str): Foreign key pointing the ego_pose.
        calibrated_sensor_token (str): Foreign key pointing the calibrated_sensor.
        filename (str): Relative path to data-blob on disk.
        fileformat (FileFormat): Data file format.
        width (int): If the sample data is an image, this is the image width in [px].
        height (int): If the sample data is an image, this is the image height in [px].
        timestamp (int): Unix time stamp.
        is_key_frame (bool): True if sample_data is part of key frame else, False.
        next (str): Foreign key pointing the sample_data that follows this in time.
            Empty if end of scene.
        prev (str): Foreign key pointing the sample_data that precedes this in time.
            Empty if start of scene.
        is_valid (bool): True if this data is valid, else False. Invalid data should be ignored.
        info_filename (str): Relative path to metainfo data-blob on disk.
        autolabel_metadata (list[AutolabelModel] | None, optional): List of models used for autolabeling applied to this entire sample_data item (e.g., image or scan).

    Shortcuts:
    ---------
        modality (SensorModality): Sensor modality. This should be set after instantiated.
        channel (str): Sensor channel. This should be set after instantiated.
    """

    sample_token: str = field(validator=validators.instance_of(str))
    ego_pose_token: str = field(validator=validators.instance_of(str))
    calibrated_sensor_token: str = field(validator=validators.instance_of(str))
    filename: str = field(validator=validators.instance_of(str))
    fileformat: FileFormat = field(converter=FileFormat)
    width: int = field(validator=validators.instance_of(int))
    height: int = field(validator=validators.instance_of(int))
    timestamp: int = field(validator=validators.instance_of(int))
    is_key_frame: bool = field(validator=validators.instance_of(bool))
    next: str = field(validator=validators.instance_of(str))  # noqa: A003
    prev: str = field(validator=validators.instance_of(str))
    is_valid: bool = field(default=True, validator=validators.instance_of(bool))
    info_filename: str | None = field(
        default=None, validator=validators.optional(validators.instance_of(str))
    )
    autolabel_metadata: list[AutolabelModel] | None = field(
        default=None,
        converter=lambda x: [
            AutolabelModel(**model) if isinstance(model, dict) else model for model in x
        ]
        if isinstance(x, list)
        else x,
        validator=validators.optional(
            validators.deep_iterable(validators.instance_of(AutolabelModel))
        ),
    )

    # shortcuts
    modality: SensorModality | None = field(init=False, default=None)
    channel: str = field(init=False, factory=str)
