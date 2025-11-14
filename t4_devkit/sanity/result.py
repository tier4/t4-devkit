from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NewType

from attrs import define, field
from tabulate import tabulate
from typing_extensions import Self

if TYPE_CHECKING:
    from .checker import RuleID, RuleName, Severity
    from .context import SanityContext

__all__ = ["Status", "Report", "SanityResult", "print_sanity_result"]


class Status(str, Enum):
    """Runtime outcome per checker."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
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
    """

    id: RuleID
    name: RuleName
    severity: Severity
    description: str
    status: Status
    reasons: list[Reason] | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.status == Status.SUCCESS:
            assert self.reasons is None, "Success report cannot have reasons"
        else:
            assert self.reasons is not None, "Non-success report must have reasons"

    def is_success(self, *, strict: bool = False) -> bool:
        """Check if the status is success."""
        return (
            self.status == Status.SUCCESS
            or self.is_skipped()
            or (not strict and self.severity.is_warning())
        )

    def is_failure(self, *, strict: bool = False) -> bool:
        """Check if the status is failure."""
        return (self.status == Status.FAILURE and self.severity.is_error()) or not (
            self.is_success(strict=strict) or self.is_skipped()
        )

    def is_skipped(self) -> bool:
        """Check if the status is skipped."""
        return self.status == Status.SKIPPED


def make_report(
    id: RuleID,
    name: RuleName,
    severity: Severity,
    description: str,
    reasons: list[Reason] | None = None,
) -> Report:
    """Make a report for the given rule."""
    if reasons:
        return Report(id, name, severity, description, Status.FAILURE, reasons)
    else:
        return Report(id, name, severity, description, Status.SUCCESS)


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

    def is_success(self, *, strict: bool = False) -> bool:
        """Return True if all reports are successful, False otherwise.

        Args:
            strict (bool): Whether to consider warnings as failures.

        Returns:
            True if all reports are successful, False otherwise.
        """
        return all(report.is_success(strict=strict) for report in self.reports)

    def to_str(self, *, strict: bool = False) -> str:
        """Return a string representation of the result.

        Args:
            strict (bool): Whether to consider warnings as failures.

        Returns:
            A string representation of the result.
        """
        string = f"=== DatasetID: {self.dataset_id} ===\n"
        for report in self.reports:
            if not report.is_success(strict=strict):
                string += f"\033[31m  {report.id}:\033[0m\n"
                for reason in report.reasons or []:
                    string += f"\033[31m     - {reason}\033[0m\n"
            elif report.is_skipped():
                string += f"\033[36m  {report.id}: [SKIPPED]\033[0m\n"
                for reason in report.reasons or []:
                    string += f"\033[36m     - {reason}\033[0m\n"
            elif report.severity.is_warning() and report.reasons:
                string += f"\033[33m  {report.id}:\033[0m\n"
                for reason in report.reasons or []:
                    string += f"\033[33m     - {reason}\033[0m\n"
            else:
                string += f"\033[32m  {report.id}: ✅\033[0m\n"
        return string


def print_sanity_result(result: SanityResult, *, strict: bool = False) -> None:
    """Print detailed and summary results of a sanity check.

    Args:
        result (SanityResult): The result of a sanity check.
    """
    # print detailed result
    print(result.to_str(strict=strict))

    # print summary result
    success = sum(1 for rp in result.reports if rp.is_success(strict=strict))
    failures = sum(1 for rp in result.reports if not rp.is_success(strict=strict))
    skips = sum(1 for rp in result.reports if rp.is_skipped())

    # just count the number of warnings
    warnings = sum(1 for rp in result.reports if rp.severity.is_warning() and rp.reasons)

    summary_rows = [
        [
            result.dataset_id,
            result.version,
            "\033[32mSUCCESS\033[0m"
            if result.is_success(strict=strict)
            else "\033[31mFAILURE\033[0m",
            len(result.reports),
            success,
            failures,
            skips,
            warnings,
        ]
    ]

    print(
        tabulate(
            summary_rows,
            headers=[
                "DatasetID",
                "Version",
                "Status",
                "Rules",
                "Success",
                "Failures",
                "Skips",
                "Warnings",
            ],
            tablefmt="pretty",
        ),
    )
