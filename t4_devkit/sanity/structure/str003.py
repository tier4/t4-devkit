from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR003"]


@CHECKERS.register()
class STR003(Checker):
    """A checker of STR003."""

    id = RuleID("STR003")
    name = RuleName("data-dir-presence")
    severity = Severity.ERROR
    description = "'data/' directory exists under the dataset root directory."

    def check(self, context: SanityContext) -> list[Reason] | None:
        match context.sensor_data_dir:
            case Some(x):
                return (
                    None
                    if x.exists()
                    else [Reason(f"Path to 'data' directory not found: {x.as_posix()}")]
                )
            case _:
                return [Reason("dataset directory doesn't contain 'data' directory")]
