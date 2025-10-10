from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import Checker, RuleID
from ..registry import CHECKERS

if TYPE_CHECKING:
    from ..context import SanityContext
    from ..result import FailureReason

__all__ = ["STR002"]


@CHECKERS.register(RuleID("STR002"))
class STR002(Checker):
    def check(self, context: SanityContext) -> list[FailureReason]:
        match context.annotation_dir:
            case Some(x):
                return (
                    []
                    if x.exists()
                    else [f"Path to 'annotation' dirrectory doesn't exist: {x.as_posix()}"]
                )
            case _:
                return ["dataset directory does't contain 'annotation' directory"]
