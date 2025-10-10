from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID
from ..registry import CHECKERS

if TYPE_CHECKING:
    from ..context import SanityContext
    from ..result import FailureReason


__all__ = ["STR001"]


@CHECKERS.register(RuleID("STR001"))
class STR001(Checker):
    def check(self, context: SanityContext) -> list[FailureReason]:
        match context.version:
            case Some(_):
                return []
            case _:
                return ["version directory doesn't exist"]
