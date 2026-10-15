from __future__ import annotations

from typing import TYPE_CHECKING

from collections import defaultdict

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC026"]


@CHECKERS.register()
class REC026(RecordsChecker):
    """A checker of REC026."""

    id = RuleID("REC026")
    name = RuleName("route-validity")
    severity = Severity.ERROR
    description = (
        "'route.valid_until' is after 'valid_from' when set, and the routes of a log do not overlap "
        "in time."
    )
    tables = (SchemaName.ROUTE,)

    def check(self, context: SanityContext) -> list[Reason] | None:
        failures = []
        by_log: dict[str, list] = defaultdict(list)
        for route in context.load_records(SchemaName.ROUTE).unwrap():
            if route.valid_until is not None and route.valid_until <= route.valid_from:
                failures.append(
                    Reason(f"Route {route.token}: 'valid_until' not after 'valid_from'")
                )
            by_log[route.log_token].append(route)
        for routes in by_log.values():
            ordered = sorted(routes, key=lambda route: route.valid_from)
            for route, following in zip(ordered, ordered[1:]):
                if route.valid_until is None or route.valid_until > following.valid_from:
                    failures.append(Reason(f"Routes {route.token} and {following.token} overlap"))
        return failures or None
