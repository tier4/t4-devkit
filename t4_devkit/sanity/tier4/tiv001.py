from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful
from returns.result import Result, safe

from t4_devkit import Tier4

from ..checker import Checker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

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
                return Nothing

    def check(self, context: SanityContext) -> list[Reason] | None:
        result = _load_tier4_safe(context)
        return (
            None if is_successful(result) else [Reason(f"Failed to load Tier4: {result.failure()}")]
        )


@safe
def _load_tier4_safe(context: SanityContext) -> Result[Tier4, Exception]:
    data_root = context.data_root.unwrap()
    revision = context.version.value_or(None)
    data_root = data_root.as_posix() if revision is None else data_root.parent.as_posix()
    return Tier4(data_root, revision=revision, verbose=False)
