from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR004"]


@CHECKERS.register(RuleID("STR004"))
class STR004(Checker):
    """A checker of STR004."""

    name = RuleName("map-dir-presence")
    severity = Severity.WARNING
    description = "'map/' directory exists under the dataset root directory."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.map_dir:
            case Some(x):
                return [] if x.exists() else [Reason(f"Path to 'map' not found: {x.as_posix()}")]
            case _:
                return [Reason("dataset directory doesn't contain 'map' directory")]
