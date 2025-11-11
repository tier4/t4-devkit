from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, NewType

from returns.maybe import Maybe, Nothing, Some

from .result import make_failure, make_skipped, make_success, make_warning

if TYPE_CHECKING:
    from .context import SanityContext
    from .result import Reason, Report


RuleID = NewType("RuleID", str)
RuleName = NewType("RuleName", str)


class Severity(str, Enum):
    """Severity levels for sanity checkers."""

    ERROR = "ERROR"
    WARNING = "WARNING"


class Checker(ABC):
    """Base class for sanity checkers."""

    name: RuleName
    description: str
    severity: Severity

    def __init__(self, id: RuleID) -> None:
        self.id = id

    def __call__(self, context: SanityContext) -> Report:
        match self.can_skip(context):
            case Some(skip):
                return make_skipped(self.id, self.name, self.severity, self.description, skip)

        reasons = self.check(context)
        if reasons:
            return (
                make_failure(self.id, self.name, self.severity, self.description, reasons)
                if self.severity == Severity.ERROR
                else make_warning(self.id, self.name, self.severity, self.description, reasons)
            )
        else:
            return make_success(self.id, self.name, self.severity, self.description)

    def can_skip(self, _: SanityContext) -> Maybe[Reason]:
        """Return a skip reason if the checker should be skipped."""
        return Nothing

    @abstractmethod
    def check(self, context: SanityContext) -> list[Reason]:
        pass
