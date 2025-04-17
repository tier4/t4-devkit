from __future__ import annotations

from typing import Sequence

import numpy as np
from attrs import define, field, validators

from t4_devkit.dataclass import SemanticLabel


@define
class FilterParams:
    """A dataclass to represent filtering parameters.

    Attributes:
        labels (Sequence[str | SemanticLabel] | None, optional): Sequence of target labels.
        uuids (Sequence[str] | None, optional): Sequence of target uuids.
        min_distance (float, optional): Minimum distance from the ego [m].
        max_distance (float, optional): Maximum distance from the ego [m].
        min_xy (tuple[float, float], optional): Minimum xy position from the ego [m].
        min_xy (tuple[float, float], optional): Maximum xy position from the ego [m].
        min_speed (float, optional): Minimum speed [m/s].
        max_speed (float, optional): Maximum speed [m/s].
        min_num_points (int): The minimum number of points which the 3D box should include.
    """

    labels: Sequence[str | SemanticLabel] | None = field(
        default=None,
        validator=validators.deep_iterable(
            validators.or_(validators.instance_of(str), validators.instance_of(SemanticLabel))
        ),
    )
    uuids: Sequence[str] | None = field(
        default=None,
        validator=validators.optional(validators.deep_iterable(validators.instance_of(str))),
    )
    min_distance: float = field(default=0.0, validator=validators.ge(0.0))
    max_distance: float = field(default=np.inf, validator=validators.ge(0.0))
    min_xy: tuple[float, float] = field(default=(-np.inf, -np.inf))
    max_xy: tuple[float, float] = field(default=(np.inf, np.inf))
    min_speed: float = field(default=0.0, validator=validators.ge(0.0))
    max_speed: float = field(default=np.inf, validator=validators.ge(0.0))
    min_num_points: int = field(
        default=0,
        validator=[validators.instance_of(int), validators.ge(0)],
    )
