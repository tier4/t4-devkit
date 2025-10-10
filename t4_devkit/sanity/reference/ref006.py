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

__all__ = ["REF006"]


@CHECKERS.register(RuleID("REF006"))
class REF006(Checker):
    """A checker of REF006."""

    name = RuleName("sample-data-to-ego-pose")
    description = "'SampleData.ego_pose_token' refers to 'EgoPose' record."

    def check(self, context: SanityContext) -> list[Reason]:
        sample_data_file = context.to_schema_file(SchemaName.SAMPLE_DATA)
        ego_pose_file = context.to_schema_file(SchemaName.EGO_POSE)
        match (sample_data_file, ego_pose_file):
            case Some(x), Some(y):
                sample_data = load_json_safe(x).unwrap()
                ego_pose_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(f"No reference to `SampleData.ego_pose_token`: {s['ego_pose_token']}")
                    for s in sample_data
                    if s["ego_pose_token"] not in ego_pose_tokens
                ]
            case _:
                return [Reason("Missing `SampleData` or `EgoPose` file")]
