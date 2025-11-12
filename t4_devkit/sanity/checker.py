from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, NewType

from returns.maybe import Maybe, Nothing, Some

from .result import make_report, make_skipped

if TYPE_CHECKING:
    from .context import SanityContext
    from .result import Reason, Report


RuleID = NewType("RuleID", str)
RuleName = NewType("RuleName", str)


class Severity(str, Enum):
    """Severity levels for sanity checkers."""

    WARNING = "WARNING"
    ERROR = "ERROR"

    def is_warning(self) -> bool:
        """Return `True` if the severity is WARNING."""
        return self == Severity.WARNING

    def is_error(self) -> bool:
        """Return `True` if the severity is ERROR."""
        return self == Severity.ERROR


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
        return make_report(
            self.id, self.name, self.severity, self.description, reasons, strict=context.strict
        )

    def can_skip(self, _: SanityContext) -> Maybe[Reason]:
        """Return a skip reason if the checker should be skipped."""
        return Nothing

    @abstractmethod
    def check(self, context: SanityContext) -> list[Reason] | None:
        """Return a list of reasons if the checker fails, or None if it passes.

        Args:
            context (SanityContext): The sanity context.

        Returns:
            A list of reasons if the checker fails, or None if it passes.
        """
        pass
