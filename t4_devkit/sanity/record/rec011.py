from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC011"]


@CHECKERS.register()
class REC011(RecordsChecker):
    """A checker of REC011."""

    id = RuleID("REC011")
    name = RuleName("point-label-indices-presence")
    severity = Severity.ERROR
    description = (
        "When a LiDAR file has 'label' / 'instance' columns, every 'Category' has an 'index', "
        "and every 'Instance' of an 'is_thing' category an 'index'."
    )
    tables = (
        SchemaName.SENSOR,
        SchemaName.CATEGORY,
        SchemaName.INSTANCE,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        columns = {
            field.name
            for sensor in context.load_records(SchemaName.SENSOR).unwrap()
            if sensor.lidar is not None
            for field in sensor.lidar.fields
        }
        categories = context.load_records(SchemaName.CATEGORY).unwrap()
        failures = []
        if "label" in columns:
            failures += [
                Reason(f"Category without 'index': {category.name}")
                for category in categories
                if category.index is None
            ]
        if "instance" in columns:
            things = {category.token for category in categories if category.is_thing}
            failures += [
                Reason(f"Instance without 'index': {instance.token}")
                for instance in context.load_records(SchemaName.INSTANCE).unwrap()
                if instance.category_token in things and instance.index is None
            ]
        return failures or None
