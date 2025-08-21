from __future__ import annotations

from attrs import converters, define, field, validators

from t4_devkit.common.converter import to_quaternion
from t4_devkit.typing import Quaternion, Vector3, Vector6

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ["EgoPose"]


@define(slots=False)
@SCHEMAS.register(SchemaName.EGO_POSE)
class EgoPose(SchemaBase):
    """A dataclass to represent schema table of `ego_pose.json`.

    Attributes:
        token (str): Unique record identifier.
        translation (Vector3): Coordinate system origin given as [x, y, z] in [m].
        rotation (Quaternion): Coordinate system orientation given as quaternion [w, x, y, z].
        timestamp (int): Unix time stamp.
        twist (Vector6 | None): Linear and angular velocities in the local coordinate system of
            the ego vehicle (in m/s for linear and rad/s for angular), in the order of
            (vx, vy, vz, yaw_rate, pitch_rate, roll_rate).
        acceleration (Vector3 | None): Acceleration in the local coordinate system of
            the ego vehicle (in m/s2), in the order of (ax, ay, az).
        geocoordinate (Vector3 | None): Coordinates in the WGS 84 reference ellipsoid
            (latitude, longitude, altitude) in degrees and meters.
    """

    translation: Vector3 = field(converter=Vector3)
    rotation: Quaternion = field(converter=to_quaternion)
    timestamp: int = field(validator=validators.instance_of(int))
    twist: Vector6 | None = field(default=None, converter=converters.optional(Vector6))
    acceleration: Vector3 | None = field(default=None, converter=converters.optional(Vector3))
    geocoordinate: Vector3 | None = field(default=None, converter=converters.optional(Vector3))
