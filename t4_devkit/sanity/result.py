from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NewType

from attrs import define
from typing_extensions import Self

if TYPE_CHECKING:
    from .checker import RuleID
    from .context import SanityContext

FailureReason = NewType("FailureReason", str)


def make_success(rule: RuleID) -> Report:
    return Report(rule, Status.SUCCESS)


def make_failure(rule: RuleID, failures: list[str]) -> Report:
    return Report(rule, Status.FAILURE, failures)


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@define
class Report:
    rule: RuleID
    status: Status
    failures: list[FailureReason] | None = None


@define
class SanityResult:
    dataset_id: str
    version: str | None
    reports: dict[str, Report]

    @classmethod
    def from_context(cls, context: SanityContext, reports: dict[str, Report]) -> Self:
        return cls(
            dataset_id=context.dataset_id.value_or("UNKNOWN"),
            version=context.version.value_or(None),
            reports=reports,
        )
