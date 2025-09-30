from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Sequence

import rerun.blueprint as rrb
from attrs import define, field

if TYPE_CHECKING:
    from t4_devkit.typing import Vector2Like


__all__ = ["ViewerConfig", "format_entity"]


@define
class ViewerConfig:
    map_entity: ClassVar[str] = "map"
    ego_entity: ClassVar[str] = "map/base_link"
    geocoordinate_entity: ClassVar[str] = "geocoordinate"
    timeline: ClassVar[str] = "timeline"

    spatial3ds: list[rrb.SpaceView] = field(factory=list)
    spatial2ds: list[rrb.SpaceView] = field(factory=list)
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
        """Return True if the configuration contains 3D view space."""
        return len(self.spatial3ds) > 0

    def has_spatial2d(self) -> bool:
        """Return True if the configuration contains 2D view space."""
        return len(self.spatial2ds) > 0


def format_entity(*entities: Sequence[str]) -> str:
    """Format entity path.

    Args:
        *entities: Entity path(s).

    Returns:
        Formatted entity path.

    Examples:
        >>> format_entity("map")
        "map"
        >>> format_entity("map", "map/base_link")
        "map/base_link"
        >>> format_entity("map", "map/base_link", "camera")
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
