from __future__ import annotations

from typing import TYPE_CHECKING

import hashlib

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF207"]


@CHECKERS.register()
class REF207(RecordsChecker):
    """A checker of REF207."""

    id = RuleID("REF207")
    name = RuleName("map-file")
    severity = Severity.ERROR
    description = "'Map.filename' exists and has the SHA-256 'Map.sha256'."
    tables = (SchemaName.MAP,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        data_root = context.data_root.unwrap()
        failures = []
        for map_ in context.load_records(SchemaName.MAP).unwrap():
            path = data_root.joinpath(map_.filename)
            if not path.exists():
                failures.append(Reason(f"Map {map_.token}: '{map_.filename}' not found"))
            elif hashlib.sha256(path.read_bytes()).hexdigest() != map_.sha256:
                failures.append(Reason(f"Map {map_.token}: SHA-256 of '{map_.filename}' differs"))
        return failures or None
