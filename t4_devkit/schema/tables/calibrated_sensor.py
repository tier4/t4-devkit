from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field

from t4_devkit.common.converter import to_quaternion

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import CamDistortionType, CamIntrinsicType, RotationType, TranslationType

__all__ = ["CalibratedSensor"]


@define(slots=False)
@SCHEMAS.register(SchemaName.CALIBRATED_SENSOR)
class CalibratedSensor(SchemaBase):
    """A dataclass to represent schema table of `calibrated_sensor.json`.

    Attributes:
        token (str): Unique record identifier.
        sensor_token (str): Foreign key pointing to the sensor type.
        translation (TranslationType): Coordinates system origin given as [x, y, z] in [m].
        rotation (RotationType): Coordinates system orientation given as quaternion [w, x, y, z].
        camera_intrinsic (CamIntrinsicType): 3x3 camera intrinsic matrix. Empty for sensors that are not cameras.
        camera_distortion (CamDistortionType): Camera distortion array. Empty for sensors that are not cameras.
    """

    sensor_token: str
    translation: TranslationType = field(converter=np.array)
    rotation: RotationType = field(converter=to_quaternion)
    camera_intrinsic: CamIntrinsicType = field(converter=np.array)
    camera_distortion: CamDistortionType = field(converter=np.array)
