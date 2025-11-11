from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["STR008"]


@CHECKERS.register(RuleID("STR008"))
class STR008(Checker):
    """A checker of STR008."""

    name = RuleName("lanelet-file-presence")
    description = "'lanelet2_map.osm' file exists under the 'map/' directory."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.map_dir:
            case Some(x):
                if not x.exists():
                    return [Reason(f"Path to 'map' directory not found: {x.as_posix()}")]
                lanelet_file = x.joinpath("lanelet2_map.osm")
                return (
                    [Reason(f"Lanelet2 map file not found: {lanelet_file.as_posix()}")]
                    if not lanelet_file.exists()
                    else []
                )
            case _:
                return [Reason("dataset directory doesn't contain 'map' directory")]
