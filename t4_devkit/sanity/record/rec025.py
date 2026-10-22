from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName, V0Converter

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC025"]


@CHECKERS.register()
class REC025(RecordsChecker):
    """A checker of REC025."""

    id = RuleID("REC025")
    name = RuleName("no-placeholder-values")
    severity = Severity.WARNING
    description = (
        "No placeholder values from loading or migrating 0.x: 'vehicle.model' and 'map.map_id' / "
        "'version_id' are not 'unknown'."
    )
    tables = (
        SchemaName.VEHICLE,
        SchemaName.MAP,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        vehicle_model = V0Converter.FALLBACKS["vehicle"]["model"]
        map_fallbacks = V0Converter.FALLBACKS["map"]
        failures = [
            Reason(f"Vehicle {vehicle.token}: placeholder 'model' {vehicle.model!r}")
            for vehicle in context.load_records(SchemaName.VEHICLE).unwrap()
            if vehicle.model == vehicle_model
        ]
        for map_record in context.load_records(SchemaName.MAP).unwrap():
            for name in ("map_id", "version_id"):
                value = getattr(map_record, name)
                if value == map_fallbacks[name]:
                    failures.append(
                        Reason(f"Map {map_record.token}: placeholder '{name}' {value!r}")
                    )
        return failures or None
