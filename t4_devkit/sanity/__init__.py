from __future__ import annotations

import warnings
from collections import defaultdict
from typing import ParamSpecArgs

from returns.pipeline import flow
from returns.result import Result, safe

from t4_devkit import Tier4
from t4_devkit.sanity.scene import SceneNumberChecker, SceneTokenChecker

from .result import SanityResult


def check_sanity(
    data_root: str,
    revision: str | None = None,
    ignore_warning: bool = True,
) -> SanityResult:
    with warnings.catch_warnings():
        if ignore_warning:
            warnings.simplefilter("ignore")
        else:
            warnings.simplefilter("error")

        t4_result = _try_tier4(data_root, revision=revision)

        # check schema tables
        schema_checkers = (SceneNumberChecker, SceneTokenChecker)

        reports = defaultdict(list)
        for checker in schema_checkers:
            reports[checker.group].extend(checker(t4))


def _try_tier4(data_root: str, revision: str | None = None) -> Result[Tier4, Exception]:
    @safe
    def _load_t4_safe(data_root: str):
        return Tier4(data_root, revision=revision, verbose=False)

    return flow(data_root, _load_t4_safe)
