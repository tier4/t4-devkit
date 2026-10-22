from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.common.io import file_sha256
from t4_devkit.schema.v1 import AssetEntry

from ..checker import ManifestChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason, make_report

if TYPE_CHECKING:
    from ..context import SanityContext
    from ..result import Report


__all__ = ["STR012"]


@CHECKERS.register()
class STR012(ManifestChecker):
    """A checker of STR012.

    Opt-in (`checksum=True`, `t4sanity --checksum`), since it reads every file, including videos
    and rosbags. Without it, the rule reports a warning that hashes were not verified.
    """

    id = RuleID("STR012")
    name = RuleName("manifest-files-checksum")
    severity = Severity.ERROR
    description = (
        "Every listed file has the listed 'sha256', and every asset the listed 'bytes'. "
        "Opt-in ('--checksum'); a warning if not run."
    )

    def __call__(self, context: SanityContext, fix: bool = False) -> Report:
        if not context.checksum:
            reasons = [Reason("Hashes not verified: run with '--checksum'")]
            return make_report(self.id, self.name, Severity.WARNING, self.description, reasons)
        return super().__call__(context, fix=fix)

    def check(self, context: SanityContext) -> list[Reason] | None:
        manifest = context.manifest.unwrap()
        data_root = context.data_root.unwrap()
        failures = []
        entries = [*manifest.tables.values(), *manifest.assets]
        for entry in entries:
            filepath = data_root.joinpath(entry.path)
            if not filepath.exists():
                continue  # reported by STR011
            if isinstance(entry, AssetEntry) and filepath.stat().st_size != entry.bytes:
                failures.append(
                    Reason(f"{entry.path}: {filepath.stat().st_size} bytes, listed {entry.bytes}")
                )
            elif file_sha256(filepath) != entry.sha256:
                failures.append(Reason(f"{entry.path}: SHA-256 differs from 'manifest.json'"))
        return failures or None
