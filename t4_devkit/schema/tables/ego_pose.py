from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from pyquaternion import Quaternion
from typing_extensions import Self

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import AccelerationType, RotationType, TranslationType, TwistType

__all__ = ("EgoPose",)


@dataclass
@SCHEMAS.register(SchemaName.EGO_POSE)
class EgoPose(SchemaBase):
    """A dataclass to represent schema table of `ego_pose.json`.

    Attributes:
        token (str): Unique record identifier.
        translation (TranslationType): Coordinate system origin given as [x, y, z] in [m].
        rotation (RotationType): Coordinate system orientation given as quaternion [w, x, y, z].
        timestamp (int): Unix time stamp.
        twist (TwistType | None): Coordinates system origin in [m/s]: (vx, vy, vz, yaw_rate, pitch_rate, roll_rate).
        acceleration (AccelerationType | None): Coordinates system origin in [m/s]: (ax, ay, az).
        geocoordinate (TranslationType | None): Coordinates system origin in the WGS 84 reference ellipsoid:
            (latitude, longitude, altitude).
    """

    token: str
    translation: TranslationType
    rotation: RotationType
    timestamp: int
    twist: TwistType | None = field(default=None)
    acceleration: AccelerationType | None = field(default=None)
    geocoordinate: TranslationType | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        new_data = data.copy()

        new_data["translation"] = np.array(data["translation"])
        new_data["rotation"] = Quaternion(data["rotation"])

        if "twist" in data:
            new_data["twist"] = np.array(data["twist"])

        if "acceleration" in data:
            new_data["acceleration"] = np.array(data["acceleration"])

        if "geocoordinate" in data:
            new_data["geocoordinate"] = np.array(data["geocoordinate"])

        return cls(**new_data)
