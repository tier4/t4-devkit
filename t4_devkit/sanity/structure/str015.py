from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from ..checker import ManifestChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR015"]


@CHECKERS.register()
class STR015(ManifestChecker):
    """A checker of STR015."""

    id = RuleID("STR015")
    name = RuleName("manifest-identity-matches-dirs")
    severity = Severity.WARNING
    description = (
        "'manifest.json' 'dataset_id' and 'version' match the names of the dataset and version "
        "directories."
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        manifest = context.manifest.unwrap()
        failures = []
        if manifest.dataset_id != context.dataset_id.unwrap():
            failures.append(
                Reason(
                    f"'dataset_id' {manifest.dataset_id!r} differs from the directory "
                    f"{context.dataset_id.unwrap()!r}"
                )
            )
        match context.version:
            case Some(directory) if str(manifest.version) != directory:
                failures.append(
                    Reason(f"'version' {manifest.version} differs from the directory {directory!r}")
                )
        return failures or None
