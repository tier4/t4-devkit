from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

import numpy as np

if TYPE_CHECKING:
    from t4_devkit.dataclass import SemanticLabel


@dataclass
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

    labels: Sequence[str | SemanticLabel] | None = field(default=None)
    uuids: Sequence[str] | None = field(default=None)
    min_distance: float = field(default=0.0)
    max_distance: float = field(default=np.inf)
    min_xy: tuple[float, float] = field(default=(-np.inf, -np.inf))
    max_xy: tuple[float, float] = field(default=(np.inf, np.inf))
    min_speed: float = field(default=0.0)
    max_speed: float = field(default=np.inf)
    min_num_points: int = field(default=0)
