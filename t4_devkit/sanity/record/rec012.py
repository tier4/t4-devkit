from __future__ import annotations

from typing import TYPE_CHECKING

from collections import Counter

from t4_devkit.schema.v1 import SchemaName

from ..checker import RecordsChecker, RuleID, RuleName, Severity
from ..registry import CHECKERS
from ..result import Reason

if TYPE_CHECKING:
    from ..context import SanityContext


__all__ = ["REC012"]


@CHECKERS.register()
class REC012(RecordsChecker):
    """A checker of REC012."""

    id = RuleID("REC012")
    name = RuleName("scene-sample-count")
    severity = Severity.ERROR
    description = "'Scene.nbr_samples' equals the number of 'Sample' records of the scene."
    tables = (
        SchemaName.SCENE,
        SchemaName.SAMPLE,
    )

    def check(self, context: SanityContext) -> list[Reason] | None:
        counts = _sample_counts(context)
        return [
            Reason(
                f"Scene {scene.token}: 'nbr_samples' {scene.nbr_samples}, has {counts[scene.token]}"
            )
            for scene in context.load_records(SchemaName.SCENE).unwrap()
            if scene.nbr_samples != counts[scene.token]
        ] or None

    def fix(self, context: SanityContext) -> bool:
        counts = _sample_counts(context)
        records = context.load_table(SchemaName.SCENE).unwrap()
        for record in records:
            record["nbr_samples"] = counts[record["token"]]
        return context.save_table(SchemaName.SCENE, records)


def _sample_counts(context: SanityContext) -> Counter[str]:
    return Counter(
        sample.scene_token for sample in context.load_records(SchemaName.SAMPLE).unwrap()
    )
