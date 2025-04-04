from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field, validators

from t4_devkit.common.converter import to_quaternion
from t4_devkit.common.validator import is_vector3

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import CamDistortionLike, CamIntrinsicLike, QuaternionLike, Vector3Like

__all__ = ["CalibratedSensor"]


@define(slots=False)
@SCHEMAS.register(SchemaName.CALIBRATED_SENSOR)
class CalibratedSensor(SchemaBase):
    """A dataclass to represent schema table of `calibrated_sensor.json`.

    Attributes:
        token (str): Unique record identifier.
        sensor_token (str): Foreign key pointing to the sensor type.
        translation (Vector3Like): Coordinates system origin given as [x, y, z] in [m].
        rotation (QuaternionLike): Coordinates system orientation given as quaternion [w, x, y, z].
        camera_intrinsic (CamIntrinsicLike): 3x3 camera intrinsic matrix. Empty for sensors that are not cameras.
        camera_distortion (CamDistortionLike): Camera distortion array. Empty for sensors that are not cameras.
    """

    sensor_token: str = field(validator=validators.instance_of(str))
    translation: Vector3Like = field(converter=np.array, validator=is_vector3)
    rotation: QuaternionLike = field(converter=to_quaternion)
    camera_intrinsic: CamIntrinsicLike = field(converter=np.array)
    camera_distortion: CamDistortionLike = field(converter=np.array)
