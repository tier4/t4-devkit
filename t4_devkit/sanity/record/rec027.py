from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity, record_name
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC027"]


@CHECKERS.register()
class REC027(RecordsChecker):
    """A checker of REC027."""

    id = RuleID("REC027")
    name = RuleName("unit-quaternions")
    severity = Severity.WARNING
    description = (
        "Rotations ('Sensor', 'EgoPose', 'SampleAnnotation', 'Route' poses) are unit quaternions."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.EGO_POSE,
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.ROUTE,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        rotations = [
            (record_name(table), record.token, record.rotation)
            for table in (SchemaName.SENSOR, SchemaName.EGO_POSE, SchemaName.SAMPLE_ANNOTATION)
            for record in context.load_records(table).unwrap()
        ] + [
            (record_name(SchemaName.ROUTE), route.token, pose.rotation)
            for route in context.load_records(SchemaName.ROUTE).unwrap()
            for pose in (route.start_pose, route.goal_pose)
        ]
        return [
            Reason(f"{table} {token}: rotation norm {rotation.norm:.6f}")
            for table, token, rotation in rotations
            if abs(rotation.norm - 1.0) > NORM_TOLERANCE
        ] or None


NORM_TOLERANCE = 1e-3
