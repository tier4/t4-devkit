from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_tier4_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["TIV001"]


@CHECKERS.register()
class TIV001(Checker):
    """A checker for TIV001."""

    id = RuleID("TIV001")
    name = RuleName("load-tier4")
    severity = Severity.ERROR
    description = "Ensure 'Tier4' instance is loaded successfully."

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match context.data_root:
            case Some(x):
                if not x.exists():
                    return Maybe.from_value(Reason(f"'{x.as_posix()}' not found"))
                return Nothing
            case _:
                return Maybe.from_value(Reason("Data root not found"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        result = load_tier4_safe(context)
        return (
            None if is_successful(result) else [Reason(f"Failed to load Tier4: {result.failure()}")]
        )
