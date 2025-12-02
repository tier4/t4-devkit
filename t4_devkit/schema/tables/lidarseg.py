from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase, impossible_empty
from .registry import SCHEMAS

__all__ = ["LidarSeg"]


@define(slots=False)
@SCHEMAS.register(SchemaName.LIDARSEG)
class LidarSeg(SchemaBase):
    """A dataclass to represent lidar point cloud segmentation data.

    Attributes:
        token (str): Unique record identifier.
        filename (str): The filename of the lidar point cloud segmentation data.
        sample_data_token (str): The token of the sample data.
    """

    filename: str = field(validator=validators.instance_of(str))
    sample_data_token: str = field(validator=(validators.instance_of(str), impossible_empty))
