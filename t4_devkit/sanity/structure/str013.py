from __future__ import annotations

from typing import TYPE_CHECKING

from ..checker import ManifestChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["STR013"]

# Directories whose files must all be listed in `manifest.json`.
LISTED_DIRS = ("annotation", "data", "map", "input_bag")


@CHECKERS.register()
class STR013(ManifestChecker):
    """A checker of STR013."""

    id = RuleID("STR013")
    name = RuleName("manifest-files-complete")
    severity = Severity.WARNING
    description = (
        "Every file under 'annotation/', 'data/', 'map/' and 'input_bag/' is listed in "
        "'manifest.json'."
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        data_root = context.data_root.unwrap()
        listed = set(context.manifest.unwrap().listed_paths())
        return [
            Reason(f"File not listed: {path}")
            for directory in LISTED_DIRS
            for path in sorted(
                filepath.relative_to(data_root).as_posix()
                for filepath in data_root.joinpath(directory).rglob("*")
                if filepath.is_file()
            )
            if path not in listed
        ] or None
