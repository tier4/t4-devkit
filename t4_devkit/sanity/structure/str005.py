from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR005"]


@CHECKERS.register(RuleID("STR005"))
class STR005(Checker):
    """A checker of STR005."""

    name = RuleName("bag-dir-presence")
    severity = Severity.WARNING
    description = "'input_bag/' directory exists under the dataset root directory."

    def check(self, context: SanityContext) -> list[Reason] | None:
        match context.bag_dir:
            case Some(x):
                return (
                    None
                    if x.exists()
                    else [Reason(f"Path to 'input_bag' not found: {x.as_posix()}")]
                )
            case _:
                return [Reason("dataset directory doesn't contain 'input_bag' directory")]
