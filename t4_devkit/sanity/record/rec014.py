from __future__ import annotations

from typing import TYPE_CHECKING

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC014"]


@CHECKERS.register()
class REC014(RecordsChecker):
    """A checker of REC014."""

    id = RuleID("REC014")
    name = RuleName("thing-category-instance")
    severity = Severity.ERROR
    description = (
        "'ObjectAnn.instance_token' is set exactly when its category has 'is_thing'; "
        "'SampleAnnotation' and 'Keypoint' instances belong to 'is_thing' categories."
    )
    tables = (
        SchemaName.CATEGORY,
        SchemaName.INSTANCE,
        SchemaName.OBJECT_ANN,
        SchemaName.SAMPLE_ANNOTATION,
        SchemaName.KEYPOINT,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        is_thing = {
            category.token: category.is_thing
            for category in context.load_records(SchemaName.CATEGORY).unwrap()
        }
        instance_category = {
            instance.token: instance.category_token
            for instance in context.load_records(SchemaName.INSTANCE).unwrap()
        }
        failures = []
        for ann in context.load_records(SchemaName.OBJECT_ANN).unwrap():
            thing = is_thing.get(ann.category_token)
            if thing is not None and thing != (ann.instance_token is not None):
                expected = "an instance" if thing else "no instance"
                failures.append(Reason(f"ObjectAnn {ann.token}: its category needs {expected}"))
        for table in (SchemaName.SAMPLE_ANNOTATION, SchemaName.KEYPOINT):
            for ann in context.load_records(table).unwrap():
                category = instance_category.get(ann.instance_token)
                if category in is_thing and not is_thing[category]:
                    failures.append(
                        Reason(
                            f"{table.value} {ann.token}: instance of a category without 'is_thing'"
                        )
                    )
        return failures or None
