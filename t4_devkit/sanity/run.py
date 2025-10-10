from __future__ import annotations

import warnings

from returns.pipeline import flow
from returns.result import Result, safe

from t4_devkit import Tier4

from .context import SanityContext
from .registry import CHECKERS
from .result import SanityResult


def check_sanity(
    data_root: str,
    revision: str | None = None,
    *,
    ignore_warnings: bool = False,
) -> SanityResult:
    with warnings.catch_warnings():
        if ignore_warnings:
            warnings.simplefilter("ignore")
        else:
            warnings.simplefilter("error")

        context = SanityContext.from_path(data_root, revision=revision)

        checkers = CHECKERS.build()
        reports = {checker.rule: checker(context) for checker in checkers}

        return SanityResult.from_context(context, reports)
        # TODO: try initializing Tier4 class at the end of checking


def _try_tier4(data_root: str, revision: str | None = None) -> Result[Tier4, Exception]:
    @safe
    def _load_t4_safe(data_root: str):
        return Tier4(data_root, revision=revision, verbose=False)

    return flow(data_root, _load_t4_safe)
