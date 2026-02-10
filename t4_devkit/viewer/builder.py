from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import rerun.blueprint as rrb
from typing_extensions import Self

from .config import EntityPath, ViewerConfig, format_entity
from .viewer import RerunViewer

if TYPE_CHECKING:
    from t4_devkit.typing import Vector2Like

__all__ = ["ViewerBuilder"]


class ViewerBuilder:
    """Builder for creating a RerunViewer instance.

    Examples:
        >>> from t4_devkit.viewer import ViewerBuilder
        >>> viewer = (
                ViewerBuilder()
                .with_spatial3d()
                .with_spatial2d(cameras=["CAM_FRONT", "CAM_BACK"])
                .with_labels(label2id={"car": 1, "pedestrian": 2})
                .with_streetmap(latlon=[48.8566, 2.3522])
                .build(app_id="my_viewer")
            )
    """

    def __init__(self) -> None:
        self._config = ViewerConfig()

    def with_spatial3d(self) -> Self:
        self._config.spatial3ds.append(rrb.Spatial3DView(name="3D", origin=EntityPath.MAP))
        return self

    def with_spatial2d(self, cameras: Sequence[str], contents: list[str] | None = None) -> Self:
        # Preserve the original contents arguments so each camera gets its own view_contents.
        base_contents = contents
        for name in cameras:
            origin = format_entity(EntityPath.BASE_LINK, name)

            default_contents = [format_entity(origin, "**")]
            view_contents = (
                default_contents if base_contents is None else default_contents + base_contents
            )

            self._config.spatial2ds.append(
                rrb.Spatial2DView(name=name, origin=origin, contents=view_contents)
            )
        return self

    def with_labels(self, label2id: dict[str, int]) -> Self:
        self._config.label2id = label2id
        return self

    def with_streetmap(self, latlon: Vector2Like | None = None) -> Self:
        self._config.spatial3ds.append(rrb.MapView(name="Map", origin=EntityPath.GEOCOORDINATE))
        if latlon is not None:
            self._config.latlon = latlon
        return self

    def build(self, app_id: str, save_dir: str | None = None) -> RerunViewer:
        return RerunViewer(app_id=app_id, config=self._config, save_dir=save_dir)
