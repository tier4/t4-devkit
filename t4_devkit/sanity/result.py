from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import NewType

from attrs import define, field

GroupName = NewType("GroupName", str)
TargetName = NewType("TargetName", str)
CheckerName = NewType("CheckerName", str)


def make_ok(checker: CheckerName) -> Report:
    return Report(checker=checker, status=Status.OK)


def make_warning(checker: CheckerName, message: str) -> Report:
    return Report(checker=checker, status=Status.WARNING, message=message)


def make_error(checker: CheckerName, message: str) -> Report:
    return Report(checker=checker, status=Status.ERROR, message=message)


class Status(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@define
class Report:
    checker: CheckerName
    status: Status
    message: str | None = None

    def is_ok(self, ignore_warning: bool) -> bool:
        return self.status == Status.OK or (ignore_warning and self.status == Status.WARNING)


@define
class SanityResult:
    dataset_id: str
    version: str | None = None
    reports: dict[GroupName, list[Report]] = field(factory=lambda: defaultdict(list))
