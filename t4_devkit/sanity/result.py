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
        if self.is_success() and self.severity.is_error():
            assert self.reasons is None, "Success report for error rule cannot have reasons"
        elif self.is_failure():
            assert self.reasons is not None, "Non-success report must have reasons"

    def is_success(self) -> bool:
        """Check if the status is success."""
        return self.status == Status.SUCCESS

    def is_failure(self) -> bool:
        """Check if the status is failure."""
        return self.status == Status.FAILURE

    def is_skipped(self) -> bool:
        """Check if the status is skipped."""
        return self.status == Status.SKIPPED


def make_report(
    id: RuleID,
    name: RuleName,
    severity: Severity,
    description: str,
    reasons: list[Reason] | None = None,
    *,
    strict: bool = False,
) -> Report:
    """Make a report for the given rule."""
    if reasons:
        if severity.is_warning():
            return (
                Report(id, name, severity, description, Status.FAILURE, reasons)
                if strict
                else Report(id, name, severity, description, Status.SUCCESS, reasons)
            )
        else:
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

    def __repr__(self) -> str:
        string = f"=== DatasetID: {self.dataset_id} ===\n"
        for report in self.reports:
            if report.is_failure():
                string += f"\033[31m  {report.id}:\033[0m\n"
                for reason in report.reasons or []:
                    string += f"\033[31m     - {reason}\033[0m\n"
            elif report.is_skipped():
                string += f"\033[36m  {report.id}: [SKIPPED]\033[0m\n"
                for reason in report.reasons or []:
                    string += f"\033[36m     - {reason}\033[0m\n"
            else:
                string += f"\033[32m  {report.id}: ✅\033[0m\n"
        return string


def print_sanity_result(result: SanityResult) -> None:
    """Print detailed and summary results of a sanity check.

    Args:
        result (SanityResult): The result of a sanity check.
    """
    # print detailed result
    print(result)

    # print summary result
    success = sum(1 for rp in result.reports if rp.is_success())
    failures = sum(1 for rp in result.reports if rp.is_failure())
    skips = sum(1 for rp in result.reports if rp.is_skipped())

    # just count the number of warnings
    warnings = sum(1 for rp in result.reports if rp.severity.is_warning() and rp.reasons)

    summary_rows = [
        [
            result.dataset_id,
            result.version,
            "\033[31mFAILURE\033[0m" if failures > 0 else "\033[32mSUCCESS\033[0m",
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
