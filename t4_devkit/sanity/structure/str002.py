from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR002"]


@CHECKERS.register(RuleID("STR002"))
class STR002(Checker):
    """A checker of STR002."""

    name = RuleName("annotation-dir-presence")
    description = "'annotation/' directory exists under the dataset root directory."

    def check(self, context: SanityContext) -> list[Reason]:
        match context.annotation_dir:
            case Some(x):
                return (
                    []
                    if x.exists()
                    else [Reason(f"Path to 'annotation' not found: {x.as_posix()}")]
                )
            case _:
                return [Reason("dataset directory doesn't contain 'annotation' directory")]
