from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["STR009"]


@CHECKERS.register(RuleID("STR009"))
class STR009(Checker):
    """A checker of STR009."""

    name = RuleName("pointcloud-map-dir-presence")
    severity = Severity.WARNING
    description = "'pointcloud_map.pcd' directory exists under the 'map/' directory."

    def check(self, context: SanityContext) -> list[Reason] | None:
        match context.map_dir:
            case Some(x):
                if not x.exists():
                    return [Reason(f"Path to 'map' directory not found: {x.as_posix()}")]
                pointcloud_map_dir = x.joinpath("pointcloud_map.pcd")
                return (
                    [Reason(f"PCD map directory not found: {pointcloud_map_dir.as_posix()}")]
                    if not pointcloud_map_dir.exists()
                    else None
                )
            case _:
                return [Reason("dataset directory doesn't contain 'map' directory")]
