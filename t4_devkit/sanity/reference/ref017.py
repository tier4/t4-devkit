from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason
from .base import missing_references

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REF017"]


@CHECKERS.register()
class REF017(RecordsChecker):
    """A checker of REF017."""

    id = RuleID("REF017")
    name = RuleName("log-and-map")
    severity = Severity.ERROR
    description = (
        "'Log.map_token' refers to 'Map' record unless it is empty, 'Map.log_tokens' refer to "
        "'Log' records, and both agree."
    )
    tables = (
        SchemaName.LOG,
        SchemaName.MAP,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        failures = missing_references(context, SchemaName.LOG, {"map_token": SchemaName.MAP})
        failures += missing_references(context, SchemaName.MAP, {"log_tokens": SchemaName.LOG})
        maps = {map_.token: map_ for map_ in context.load_records(SchemaName.MAP).unwrap()}
        for log in context.load_records(SchemaName.LOG).unwrap():
            if log.map_token in maps and log.token not in maps[log.map_token].log_tokens:
                failures.append(Reason(f"Log {log.token}: its map does not list it"))
            for map_ in maps.values():
                if log.token in map_.log_tokens and log.map_token != map_.token:
                    failures.append(Reason(f"Log {log.token}: listed by map {map_.token}"))
        return failures or None
