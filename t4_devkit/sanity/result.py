from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, ClassVar, NewType

from attrs import define, field
from tabulate import tabulate
from typing_extensions import Self

if TYPE_CHECKING:
    from .checker import RuleID, RuleName, Severity
    from .context import SanityContext

__all__ = ["Status", "Report", "SanityResult", "print_sanity_result"]


class Status(str, Enum):
    """Runtime outcome per checker."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


Reason = NewType("Reason", str)


@define
class Report:
    """A report for a rule.

    Attributes:
        id (RuleID): The ID of the rule.
        name (RuleName): The name of the rule.
        severity (Severity): The severity of the rule.
        description (str): The description of the rule.
        status (Status): The status of the report.
        reasons (list[Reason] | None): The list of reasons for the report if the report is a failure or skipped.
        fixed (bool): Whether the report is fixed.
    """

    id: RuleID
    name: RuleName
    severity: Severity
    description: str
    status: Status
    reasons: list[Reason] | None = field(default=None)
    fixed: bool = False

    PALETTE: ClassVar[dict[str, str]] = {
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "CYAN": "\033[36m",
    }

    def __attrs_post_init__(self) -> None:
        if self.status == Status.PASSED:
            assert self.reasons is None, "Passed report cannot have reasons"
        else:
            assert self.reasons is not None, "Non-passed report must have reasons"

    def is_passed(self, *, strict: bool = False) -> bool:
        """Check if the status is passed."""
        return (
            self.status == Status.PASSED
            or self.is_skipped()
            or (not strict and self.severity.is_warning())
            or self.fixed
        )

    def is_failed(self, *, strict: bool = False) -> bool:
        """Check if the status is failed."""
        return (self.status == Status.FAILED and self.severity.is_error()) or not (
            self.is_passed(strict=strict) or self.is_skipped()
        )

    def is_skipped(self) -> bool:
        """Check if the status is skipped."""
        return self.status == Status.SKIPPED

    def to_str(self, *, strict: bool = False) -> str:
        """Return a string representation of the report.

        Args:
            strict (bool): Whether to consider warnings as failures.

        Returns:
            A string representation of the report.
        """
        parts = []
        if not self.is_passed(strict=strict):
            # print failure reasons
            color = self.PALETTE["RED"]
            parts.append(f"{color}  {self.id}:\033[0m\n")
            for reason in self.reasons or []:
                parts.append(f"{color}     - {reason}\033[0m\n")
        elif self.is_skipped():
            # print skipped reasons
            color = self.PALETTE["CYAN"]
            parts.append(f"{color}  {self.id}: [SKIPPED]\033[0m\n")
            for reason in self.reasons or []:
                parts.append(f"{color}     - {reason}\033[0m\n")
        elif self.severity.is_warning() and self.reasons:
            # print warning reasons
            color = self.PALETTE["YELLOW"]
            parts.append(f"{color}  {self.id}:\033[0m\n")
            for reason in self.reasons or []:
                parts.append(f"{color}     - {reason}\033[0m\n")
        elif self.is_passed() and self.fixed:
            # print failure or warning but fixed reasons
            color1 = self.PALETTE["YELLOW"] if self.severity.is_warning() else self.PALETTE["RED"]
            color2 = self.PALETTE["GREEN"]
            parts.append(f"{color1}  {self.id}:\033[0m {color2}--> FIXED🎉\033[0m\n")
            for reason in self.reasons or []:
                parts.append(f"{color1}     - {reason}\033[0m\n")
        else:
            # print passed
            color = self.PALETTE["GREEN"]
            parts.append(f"{color}  {self.id}: ✅\033[0m\n")
        return "".join(parts)


def make_report(
    id: RuleID,
    name: RuleName,
    severity: Severity,
    description: str,
    reasons: list[Reason] | None = None,
    fixed: bool = False,
) -> Report:
    """Make a report for the given rule."""
    if reasons:
        return Report(id, name, severity, description, Status.FAILED, reasons, fixed)
    else:
        return Report(id, name, severity, description, Status.PASSED)


def make_skipped(
    id: RuleID, name: RuleName, severity: Severity, description: str, reason: Reason
) -> Report:
    """Make a skipped report for the given rule."""
    return Report(id, name, severity, description, Status.SKIPPED, [reason])


@define
class SanityResult:
    """The result of a Sanity check.

    Attributes:
        dataset_id (str): The ID of the dataset.
        version (str | None): The version of the dataset.
        reports (list[Report]): The list of reports.
    """

    dataset_id: str
    version: str | None
    reports: list[Report]

    @classmethod
    def from_context(cls, context: SanityContext, reports: list[Report]) -> Self:
        """Create a SanityResult from a SanityContext and a list of reports.

        Args:
            context (SanityContext): The SanityContext to use.
            reports (list[Report]): The list of reports to include in the result.

        Returns:
            The created SanityResult.
        """
        return cls(
            dataset_id=context.dataset_id.value_or("UNKNOWN"),
            version=context.version.value_or(None),
            reports=reports,
        )

    def is_passed(self, *, strict: bool = False) -> bool:
        """Return True if all reports are passed, False otherwise.

        Args:
            strict (bool): Whether to consider warnings as failures.

        Returns:
            True if all reports are passed, False otherwise.
        """
        return all(report.is_passed(strict=strict) for report in self.reports)

    def to_str(self, *, strict: bool = False) -> str:
        """Return a string representation of the result.

        Args:
            strict (bool): Whether to consider warnings as failures.

        Returns:
            A string representation of the result.
        """
        return f"=== DatasetID: {self.dataset_id} ===\n" + "".join(
            report.to_str(strict=strict) for report in self.reports
        )


def print_sanity_result(result: SanityResult, *, strict: bool = False) -> None:
    """Print detailed and summary results of a sanity check.

    Args:
        result (SanityResult): The result of a sanity check.
    """
    # print detailed result
    print(result.to_str(strict=strict))

    # print summary result
    passed = sum(1 for rp in result.reports if rp.is_passed(strict=strict))
    failed = sum(1 for rp in result.reports if not rp.is_passed(strict=strict))
    skipped = sum(1 for rp in result.reports if rp.is_skipped())

    # just count the number of warnings
    warnings = sum(1 for rp in result.reports if rp.severity.is_warning() and rp.reasons)

    # count the number of fixed issues
    fixed = sum(1 for rp in result.reports if rp.fixed)

    summary_rows = [[result.dataset_id, result.version, passed, failed, skipped, warnings, fixed]]

    print(
        tabulate(
            summary_rows,
            headers=["DatasetID", "Version", "Passed", "Failed", "Skipped", "Warnings", "Fixed"],
            tablefmt="pretty",
        ),
    )
