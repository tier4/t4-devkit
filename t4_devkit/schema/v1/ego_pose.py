from __future__ import annotations

from enum import Enum, unique

from attrs import converters, define, field, validators

from t4_devkit.common.converter import to_quaternion
from t4_devkit.schema.tables.base import SchemaBase, impossible_empty
from t4_devkit.typing import Quaternion, Vector3, Vector6

__all__ = ["EgoPoseSource", "EgoPose"]


@unique
class EgoPoseSource(str, Enum):
    """Where an ego pose came from."""

    LOCALIZATION = "localization"
    POST_PROCESSED = "post_processed"
    GNSS_INS = "gnss_ins"


@define(slots=False)
class EgoPose(SchemaBase):
    """`ego_pose.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        translation (Vector3): Position in `frame`, given as [x, y, z] in [m].
        rotation (Quaternion): Orientation in `frame`, given as quaternion [w, x, y, z].
        timestamp (int): Unix time stamp [us].
        twist (Vector6 | None): (vx, vy, vz, yaw_rate, pitch_rate, roll_rate) in the vehicle frame.
        acceleration (Vector3 | None): (ax, ay, az) in the vehicle frame [m/s^2].
        geocoordinate (Vector3 | None): (latitude, longitude, altitude).
        source (EgoPoseSource): Where the pose came from.
        frame (str): Coordinate frame of the pose, e.g. "map".
        covariance (list[float] | None): 6x6 pose covariance, row-major.
    """

    translation: Vector3 = field(converter=Vector3)
    rotation: Quaternion = field(converter=to_quaternion)
    timestamp: int = field(validator=validators.instance_of(int))
    twist: Vector6 | None = field(converter=converters.optional(Vector6))
    acceleration: Vector3 | None = field(converter=converters.optional(Vector3))
    geocoordinate: Vector3 | None = field(converter=converters.optional(Vector3))
    source: EgoPoseSource = field(converter=EgoPoseSource)
    frame: str = field(validator=(validators.instance_of(str), impossible_empty()))
    covariance: list[float] | None = field(
        validator=validators.optional(
            validators.deep_iterable(
                validators.instance_of((int, float)),
                (validators.instance_of(list), validators.min_len(36), validators.max_len(36)),
            )
        )
    )
