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
        RotationType,
        SizeType,
        TranslationType,
        VelocityType,
    )

__all__ = ["SampleAnnotation"]


@define(slots=False)
@SCHEMAS.register(SchemaName.SAMPLE_ANNOTATION)
class SampleAnnotation(SchemaBase):
    """A dataclass to represent schema table of `sample_annotation.json`.

    Attributes:
        token (str): Unique record identifier.
        sample_token (str): Foreign key pointing the sample.
        instance_token (str): Foreign key pointing the object instance.
        attribute_tokens (list[str]): Foreign keys. List of attributes for this annotation.
        visibility_token (str): Foreign key pointing the object visibility.
        translation (TranslationType): Bounding box location given as [x, y, z] in [m].
        size (SizeType): Bounding box size given as [width, length, height] in [m].
        rotation (RotationType): Bounding box orientation given as quaternion [w, x, y, z].
        num_lidar_pts (int): Number of lidar points in this box.
        num_radar_pts (int): Number of radar points in this box.
        next (str): Foreign key pointing the annotation that follows this in time.
            Empty if this is the last annotation for this object.
        prev (str): Foreign key pointing the annotation that precedes this in time.
            Empty if this the first annotation for this object.
        velocity (VelocityType | None, optional): Bounding box velocity given as
            [vx, vy, vz] in [m/s].
        acceleration (AccelerationType | None, optional): Bonding box acceleration
            given as [ax, ay, av] in [m/s^2].

    Shortcuts:
    ---------
        category_name (str): Category name. This should be set after instantiated.
    """

    sample_token: str
    instance_token: str
    attribute_tokens: list[str]
    visibility_token: str
    translation: TranslationType = field(converter=np.array)
    size: SizeType = field(converter=np.array)
    rotation: RotationType = field(converter=to_quaternion)
    num_lidar_pts: int
    num_radar_pts: int
    next: str  # noqa: A003
    prev: str
    velocity: VelocityType | None = field(default=None, converter=optional(np.array))
    acceleration: AccelerationType | None = field(default=None, converter=optional(np.array))

    # shortcuts
    category_name: str = field(init=False, factory=str)
