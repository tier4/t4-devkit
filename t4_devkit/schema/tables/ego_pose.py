from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field

from t4_devkit.common.converter import as_quaternion

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import RotationType, TranslationType

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
    """

    translation: TranslationType = field(converter=np.asarray)
    rotation: RotationType = field(converter=as_quaternion)
    timestamp: int
