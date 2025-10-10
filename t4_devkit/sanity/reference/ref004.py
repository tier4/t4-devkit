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

__all__ = ["REF004"]


@CHECKERS.register(RuleID("REF004"))
class REF004(Checker):
    """A checker of REF004."""

    name = RuleName("sample-to-scene")
    description = "'Sample.scene_token' refers to 'Scene' record."

    def check(self, context: SanityContext) -> list[Reason]:
        sample_file = context.to_schema_file(SchemaName.SAMPLE)
        scene_file = context.to_schema_file(SchemaName.SCENE)
        match (sample_file, scene_file):
            case Some(x), Some(y):
                sample = load_json_safe(x).unwrap()
                scene_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(f"No reference to `Sample.scene_token`: {s['scene_token']}")
                    for s in sample
                    if s["scene_token"] not in scene_tokens
                ]
            case _:
                return [Reason("Missing `Scene` or `Sample` file")]
