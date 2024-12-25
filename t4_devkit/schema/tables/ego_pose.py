from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field
from attrs.converters import optional

from t4_devkit.common.converter import to_quaternion

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import (
        AccelerationType,
        GeoCoordinateType,
        RotationType,
        TranslationType,
        TwistType,
    )

__all__ = ["EgoPose"]


@define(slots=False)
@SCHEMAS.register(SchemaName.EGO_POSE)
class EgoPose(SchemaBase):
    """A dataclass to represent schema table of `ego_pose.json`.

    Attributes:
        token (str): Unique record identifier.
        translation (TranslationType): Coordinate system origin given as [x, y, z] in [m].
        rotation (RotationType): Coordinate system orientation given as quaternion [w, x, y, z].
        timestamp (int): Unix time stamp.
        twist (TwistType | None): Linear and angular velocities in the local coordinate system of
            the ego vehicle (in m/s for linear and rad/s for angular), in the order of
            (vx, vy, vz, yaw_rate, pitch_rate, roll_rate).
        acceleration (AccelerationType | None): Acceleration in the local coordinate system of
            the ego vehicle (in m/s2), in the order of (ax, ay, az).
        geocoordinate (GeoCoordinateType | None): Coordinates in the WGS 84 reference ellipsoid
            (latitude, longitude, altitude) in degrees and meters.
    """

    translation: TranslationType = field(converter=np.array)
    rotation: RotationType = field(converter=to_quaternion)
    timestamp: int
    twist: TwistType | None = field(default=None, converter=optional(np.array))
    acceleration: AccelerationType | None = field(default=None, converter=optional(np.array))
    geocoordinate: GeoCoordinateType | None = field(default=None, converter=optional(np.array))
