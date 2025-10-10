from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NewType

from .result import make_failure, make_success

if TYPE_CHECKING:
    from .context import SanityContext
    from .result import FailureReason, Report


RuleID = NewType("RuleID", str)


class Checker(ABC):
    """Base class for sanity checkers."""

    def __init__(self, rule: RuleID) -> None:
        self.rule = rule

    def __call__(self, context: SanityContext) -> Report:
        failures = self.check(context)
        if failures:
            return make_failure(self.rule, failures)
        else:
            return make_success(self.rule)

    @abstractmethod
    def check(self, context: SanityContext) -> list[FailureReason]:
        pass
