from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, NewType

from returns.maybe import Maybe, Nothing, Some

from .result import Reason, make_report, make_skipped

if TYPE_CHECKING:
    from .context import SanityContext
    from .result import Report


RuleID = NewType("RuleID", str)
RuleName = NewType("RuleName", str)


class SchemaVersion(str, Enum):
    """Dataset schema versions a rule can apply to."""

    V0 = "0.x"
    V1 = "1.0"


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
    """Base class for sanity checkers.

    Attributes:
        versions (tuple[SchemaVersion, ...]): Schema versions the rule applies to; 0.x by default.
    """

    id: RuleID
    name: RuleName
    description: str
    severity: Severity
    versions: tuple[SchemaVersion, ...] = (SchemaVersion.V0,)

    def __call__(self, context: SanityContext, fix: bool = False) -> Report:
        """Run the checker and return a report.

        The issues will be fixed if the checker is fixable, `fix` is True and
            the checker returns a list of failure or warning reasons (not `None`).

        Args:
            context (SanityContext): The sanity context.
            fix (bool, optional): Whether to attempt to fix the issue.

        Returns:
            A report containing the results of the checker.
        """
        match self.can_skip(context):
            case Some(skip):
                return make_skipped(self.id, self.name, self.severity, self.description, skip)

        reasons = self.check(context)
        fixed = self.fix(context) if fix and reasons else False
        return make_report(self.id, self.name, self.severity, self.description, reasons, fixed)

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        """Return a skip reason if the checker should be skipped.

        Args:
            context (SanityContext): The sanity context.

        Returns:
            A skip reason if the checker should be skipped, or Nothing if it should not be skipped.
        """
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

    def fix(self, context: SanityContext) -> bool:
        """Fix the issue reported by the checker.

        Args:
            context (SanityContext): The sanity context.

        Returns:
            True if the issue was fixed, False otherwise.
        """
        return False


class ManifestChecker(Checker):
    """Base class for 1.0 rules that read `manifest.json`: skipped when it cannot be read or is
    not valid (reported by STR010 and FMT020)."""

    versions = (SchemaVersion.V1,)

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match context.manifest:
            case Some(_):
                return Nothing
        return Maybe.from_value(Reason("No valid 'manifest.json' (see STR010, FMT020)"))
