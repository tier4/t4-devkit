from __future__ import annotations

import warnings
from typing import Sequence

from .context import SanityContext
from .registry import CHECKERS
from .result import SanityResult

__all__ = ["sanity_check"]


def sanity_check(
    data_root: str,
    revision: str | None = None,
    *,
    include_warning: bool = False,
    excludes: Sequence[str] | None = None,
) -> SanityResult:
    with warnings.catch_warnings():
        if include_warning:
            warnings.simplefilter("error")
        else:
            warnings.simplefilter("ignore")

        context = SanityContext.from_path(data_root, revision=revision)

        checkers = CHECKERS.build(excludes=excludes)
        reports = [checker(context) for checker in checkers]

        return SanityResult.from_context(context, reports)
