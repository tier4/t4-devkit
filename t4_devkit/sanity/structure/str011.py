from __future__ import annotations

from typing import TYPE_CHECKING

from ..checker import ManifestChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR011"]


@CHECKERS.register()
class STR011(ManifestChecker):
    """A checker of STR011."""

    id = RuleID("STR011")
    name = RuleName("manifest-files-presence")
    severity = Severity.ERROR
    description = "Every file listed in 'manifest.json' ('tables' and 'assets') exists."

    def check(self, context: SanityContext) -> list[Reason] | None:
        data_root = context.data_root.unwrap()
        return [
            Reason(f"Listed file not found: {path}")
            for path in context.manifest.unwrap().listed_paths()
            if not data_root.joinpath(path).exists()
        ] or None
