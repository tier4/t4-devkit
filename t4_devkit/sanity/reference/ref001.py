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

__all__ = ["REF001"]


@CHECKERS.register(RuleID("REF001"))
class REF001(Checker):
    """A checker of REF001."""

    name = RuleName("scene-to-log")
    description = "'Scene.log_token' refers to 'Log' record."

    def check(self, context: SanityContext) -> list[Reason]:
        scene_file = context.to_schema_file(SchemaName.SCENE)
        log_file = context.to_schema_file(SchemaName.LOG)
        match (scene_file, log_file):
            case Some(x), Some(y):
                scene = load_json_safe(x).unwrap()
                log_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(f"No reference to `Scene.log_token`: {s['log_token']}")
                    for s in scene
                    if s["log_token"] not in log_tokens
                ]
            case _:
                return [Reason("Missing `Scene` or `Log` file")]
