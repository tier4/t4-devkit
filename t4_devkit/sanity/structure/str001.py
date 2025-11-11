from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR001"]


@CHECKERS.register(RuleID("STR001"))
class STR001(Checker):
    """A checker of STR001."""

    name = RuleName("version-dir-presence")
    severity = Severity.WARNING
    description = "'version/' directory exists under the dataset root directory."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.version:
            case Some(_):
                return []
            case _:
                return [Reason("'version' directory doesn't exist")]
