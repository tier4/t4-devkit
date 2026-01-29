from __future__ import annotations

from typing import Sequence

from .context import SanityContext
from .registry import CHECKERS
from .result import SanityResult

__all__ = ["sanity_check"]


def sanity_check(
    data_root: str,
    revision: str | None = None,
    *,
    excludes: Sequence[str] | None = None,
    fix: bool = False,
) -> SanityResult:
    """Run sanity checks on the given data root.

    Args:
        data_root (str): The root directory of the data.
        revision (str | None, optional): The revision to check. If None, the latest revision is used.
        excludes (Sequence[str] | None, optional): A list of rule names or groups to exclude.
        fix (bool, optional): Attempt to fix the issues reported by the sanity check.

    Returns:
        A SanityResult object.
    """
    context = SanityContext.from_path(data_root, revision=revision)

    checkers = CHECKERS.build(excludes=excludes)
    reports = [checker(context, fix=fix) for checker in checkers]

    return SanityResult.from_context(context, reports)
