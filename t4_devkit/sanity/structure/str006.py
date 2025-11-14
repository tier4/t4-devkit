from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR006"]


@CHECKERS.register()
class STR006(Checker):
    """A checker of STR006."""

    id = RuleID("STR006")
    name = RuleName("status-json-presence")
    severity = Severity.WARNING
    description = "'status.json' file exists under the dataset root directory."

    def check(self, context: SanityContext) -> list[Reason] | None:
        match context.status_json:
            case Some(x):
                return (
                    None
                    if x.exists()
                    else [Reason(f"Path to 'status.json' not found: {x.as_posix()}")]
                )
            case _:
                return [Reason("dataset directory doesn't contain 'status.json' file")]
