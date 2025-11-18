from __future__ import annotations

import pytest

from t4_devkit.sanity.checker import RuleID, RuleName, Severity
from t4_devkit.sanity.result import Reason, Report, SanityResult, Status, make_report, make_skipped


@pytest.mark.parametrize(
    ["severity", "reasons"],
    [
        (Severity.ERROR, None),
        (Severity.WARNING, None),
        (Severity.ERROR, Reason("Failed reason")),
        (Severity.WARNING, Reason("Failed reason")),
    ],
)
def test_make_report(severity: Severity, reasons: list[Reason] | None) -> None:
    """Test the make_report function."""
    report = make_report(
        id=RuleID("STR000"),
        name=RuleName("custom-checker"),
        severity=severity,
        description="This is a custom checker.",
        reasons=reasons,
    )
    if reasons:
        assert report.status == Status.FAILED, f"Expected FAILED status, got {report.status}"
    else:
        assert report.status == Status.PASSED, f"Expected PASSED status, got {report.status}"


def test_make_skipped() -> None:
    """Test the make_skipped function."""
    report = make_skipped(
        id=RuleID("STR000"),
        name=RuleName("custom-checker"),
        severity=Severity.ERROR,
        description="This is a custom checker.",
        reason=Reason("Skipped reason"),
    )
    assert report.status == Status.SKIPPED, f"Expected SKIPPED status, got {report.status}"


@pytest.mark.parametrize("strict", [True, False])
def test_sanity_result(strict: bool) -> None:
    """Test the SanityResult class.

    Note:
        When strict=True, SanityResult.is_passed(strict) should return True if all reports are passed.
        Otherwise, it should return True even if at least one report whose severity is WARNING failed.
    """
    reports = [
        Report(
            id=RuleID("STR000"),
            name=RuleName("custom-checker0"),
            severity=Severity.ERROR,
            description="This is a custom checker0.",
            status=Status.PASSED,
            reasons=None,
        ),
        Report(
            id=RuleID("STR001"),
            name=RuleName("custom-checker1"),
            severity=Severity.WARNING,
            description="This is a custom checker1.",
            status=Status.PASSED,
            reasons=None,
        ),
        Report(
            id=RuleID("STR002"),
            name=RuleName("custom-checker2"),
            severity=Severity.WARNING,
            description="This is a custom checker2.",
            status=Status.FAILED,
            reasons=[Reason("Failed reason2")],
        ),
    ]
    result = SanityResult("test-dataset", "0", reports=reports)
    if strict:
        assert result.is_passed(strict=strict) is False
    else:
        assert result.is_passed(strict=strict)
