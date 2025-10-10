from __future__ import annotations

from typing import TYPE_CHECKING

from returns.maybe import Some

from t4_devkit.schema import SchemaName

from ..checker import Checker, RuleID, RuleName
from ..registry import CHECKERS
from ..result import Reason
from ..safety import load_json_safe

if TYPE_CHECKING:
    from ..context import SanityContext

__all__ = ["REF003"]


@CHECKERS.register(RuleID("REF003"))
class REF003(Checker):
    """A checker of REF003."""

    name = RuleName("scene-to-last-sample")
    description = "'Scene.last_sample_token' refers to 'Sample' record."

    def check(self, context: SanityContext) -> list[Reason]:
        scene_file = context.to_schema_file(SchemaName.SCENE)
        sample_file = context.to_schema_file(SchemaName.SAMPLE)
        match (scene_file, sample_file):
            case Some(x), Some(y):
                scene = load_json_safe(x).unwrap()
                sample_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(f"No reference to `Scene.last_sample_token`: {s['last_sample_token']}")
                    for s in scene
                    if s["last_sample_token"] not in sample_tokens
                ]
            case _:
                return [Reason("Missing `Scene` or `Sample` file")]
