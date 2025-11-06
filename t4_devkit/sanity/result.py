from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NewType

from attrs import define, field
from tabulate import tabulate
from typing_extensions import Self

if TYPE_CHECKING:
    from .checker import RuleID, RuleName
    from .context import SanityContext

__all__ = ["Status", "Report", "SanityResult", "print_sanity_result"]


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"

    def is_success(self) -> bool:
        return self == Status.SUCCESS

    def is_failure(self) -> bool:
        return self == Status.FAILURE

    def is_skipped(self) -> bool:
        return self == Status.SKIPPED


Reason = NewType("Reason", str)


@define
class Report:
    id: RuleID
    name: RuleName
    description: str
    status: Status
    reasons: list[Reason] | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.is_success():
            assert self.reasons is None, "Success report cannot have reasons"
        else:
            assert self.reasons is not None, "Failure report must have reasons"

    def is_success(self) -> bool:
        return self.status == Status.SUCCESS

    def is_failure(self) -> bool:
        return self.status == Status.FAILURE

    def is_skipped(self) -> bool:
        return self.status == Status.SKIPPED


def make_success(id: RuleID, name: RuleName, description: str) -> Report:
    """Make a success report for the given rule."""
    return Report(id, name, description, Status.SUCCESS)


def make_skipped(id: RuleID, name: RuleName, description: str, reason: Reason) -> Report:
    """Make a skipped report for the given rule."""
    return Report(id, name, description, Status.SKIPPED, [reason])


def make_failure(id: RuleID, name: RuleName, description: str, reasons: list[Reason]) -> Report:
    """Make a failure report for the given rule."""
    return Report(id, name, description, Status.FAILURE, reasons)


@define
class SanityResult:
    dataset_id: str
    version: str | None
    reports: list[Report]

    @classmethod
    def from_context(cls, context: SanityContext, reports: list[Report]) -> Self:
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
                string += f"\033[33m  {report.id}:\033[0m\n"
                for reason in report.reasons or []:
                    string += f"\033[33m     - {reason}\033[0m\n"
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
    summary_rows = [
        [
            result.dataset_id,
            result.version,
            "\033[31mFAILURE\033[0m" if failures > 0 else "\033[32mSUCCESS\033[0m",
            len(result.reports),
            success,
            failures,
            skips,
        ]
    ]

    print(
        tabulate(
            summary_rows,
            headers=["DatasetID", "Version", "Status", "Rules", "Success", "Failures", "Skips"],
            tablefmt="pretty",
        ),
    )
