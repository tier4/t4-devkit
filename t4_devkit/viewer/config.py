from __future__ import annotations

from enum import Enum, unique
from typing import TYPE_CHECKING

import rerun.blueprint as rrb
from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.typing import Vector2Like


__all__ = ["EntityPath", "ViewerConfig", "format_entity"]


@unique
class EntityPath(str, Enum):
    """Entity path enumerations."""

    TIMELINE = "timeline"
    MAP = "map"
    BASE_LINK = "map/base_link"
    GEOCOORDINATE = "geocoordinate"
    VECTOR_MAP = "vector_map"
    BOX = "box"
    VELOCITY = "velocity"
    FUTURE = "future"
    SEGMENTATION = "segmentation"


@define
class ViewerConfig:
    """Viewer configuration.

    Attributes:
        spatial3ds (list[rrb.Spatial3DView] | rrb.MapView): List of 3D spatial views.
        spatial2ds (list[rrb.Spatial2Dview]): List of 2D spatial views.
        label2id (dict[str, int]): Key-value mapping to convert label name to its ID.
        latlon (Vector2Like | None): Starting point in (latitude, longitude).
    """

    spatial3ds: list[rrb.Spatial3DView | rrb.MapView] = field(factory=list)
    spatial2ds: list[rrb.Spatial2DView] = field(factory=list)
    label2id: dict[str, int] = field(factory=dict)
    latlon: Vector2Like | None = field(default=None)

    def to_blueprint(self) -> rrb.BlueprintLike:
        """Return the recording blueprint."""
        views = []
        if self.spatial3ds:
            views.append(rrb.Horizontal(*self.spatial3ds, column_shares=[3, 1]))
        if self.spatial2ds:
            views.append(rrb.Grid(*self.spatial2ds))

        return rrb.Vertical(*views, row_shares=[4, 2])

    def has_spatial3d(self) -> bool:
        """Return `True` if the configuration contains 3D view space."""
        return len(self.spatial3ds) > 0

    def has_spatial2d(self) -> bool:
        """Return `True` if the configuration contains 2D view space."""
        return len(self.spatial2ds) > 0


def format_entity(*entities: str | EntityPath) -> str:
    """Format entity path.

    Args:
        *entities (str | EntityPath): Entity path(s).

    Returns:
        Formatted entity path.

    Examples:
        >>> format_entity("map")
        "map"
        >>> format_entity("map", "map/base_link")
        "map/base_link"
        >>> format_entity("map", "map/base_link", "camera")
        "map/base_link/camera"
        >>> format_entity(EntityPath.BASE_LINK, "camera")
        "map/base_link/camera"
    """
    if not entities:
        return ""

    flattened = []
    for entity in entities:
        for part in entity.split("/"):
            if part and flattened and flattened[-1] == part:
                continue
            flattened.append(part)
    return "/".join(flattened)
