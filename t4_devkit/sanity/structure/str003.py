from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID
from ..registry import CHECKERS

if TYPE_CHECKING:
    from ..context import SanityContext
    from ..result import FailureReason


@CHECKERS.register(RuleID("STR003"))
class STR003(Checker):
    def check(self, context: SanityContext) -> list[FailureReason]:
        match context.sensor_data_dir:
            case Some(x):
                return (
                    []
                    if x.exists()
                    else [f"Path to 'data' directory doesn't exist: {x.as_posix()}"]
                )
            case _:
                return ["dataset directory does't contain 'data' directory"]
