from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Maybe, Nothing, Some
from returns.pipeline import is_successful

from t4_devkit.schema.v1 import MANIFEST_FILENAME

from ..checker import Checker, RuleID, RuleName, SchemaVersion, Severity
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_manifest_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["FMT020"]


@CHECKERS.register()
class FMT020(Checker):
    """A checker of FMT020."""

    id = RuleID("FMT020")
    name = RuleName("manifest-field")
    severity = Severity.ERROR
    description = "All 'manifest.json' fields are valid."
    versions = (SchemaVersion.V1,)

    def can_skip(self, context: SanityContext) -> Maybe[Reason]:
        match context.raw_manifest:
            case Some(_):
                return Nothing
        return Maybe.from_value(Reason(f"'{MANIFEST_FILENAME}' cannot be read (see STR010)"))

    def check(self, context: SanityContext) -> list[Reason] | None:
        result = load_manifest_safe(context.raw_manifest.unwrap())
        return None if is_successful(result) else [Reason(f"{result.failure()}")]
