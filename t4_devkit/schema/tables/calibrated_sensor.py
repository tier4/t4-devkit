from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.common.converter import to_quaternion
from t4_devkit.typing import CameraDistortion, CameraIntrinsic, Quaternion, Vector3

from ..name import SchemaName
from .base import SchemaBase, impossible_empty
from .registry import SCHEMAS

__all__ = ["CalibratedSensor"]


@define(slots=False)
@SCHEMAS.register(SchemaName.CALIBRATED_SENSOR)
class CalibratedSensor(SchemaBase):
    """A dataclass to represent schema table of `calibrated_sensor.json`.

    Attributes:
        token (str): Unique record identifier.
        sensor_token (str): Foreign key pointing to the sensor type.
        translation (Vector3): Coordinates system origin given as [x, y, z] in [m].
        rotation (Quaternion): Coordinates system orientation given as quaternion [w, x, y, z].
        camera_intrinsic (CameraIntrinsic): 3x3 camera intrinsic matrix. Empty for sensors that are not cameras.
        camera_distortion (CameraDistortion): Camera distortion array. Empty for sensors that are not cameras.
    """

    sensor_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    translation: Vector3 = field(converter=Vector3)
    rotation: Quaternion = field(converter=to_quaternion)
    camera_intrinsic: CameraIntrinsic = field(converter=CameraIntrinsic)
    camera_distortion: CameraDistortion = field(converter=CameraDistortion)
