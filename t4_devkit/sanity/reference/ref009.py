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

__all__ = ["REF009"]


@CHECKERS.register(RuleID("REF009"))
class REF009(Checker):
    """A checker of REF009."""

    name = RuleName("instance-to-category")
    description = "'Instance.category_token' refers to 'Category' record."

    def check(self, context: SanityContext) -> list[Reason]:
        instance_file = context.to_schema_file(SchemaName.INSTANCE)
        category_file = context.to_schema_file(SchemaName.CATEGORY)
        match (instance_file, category_file):
            case Some(x), Some(y):
                instance = load_json_safe(x).unwrap()
                category_tokens = [item["token"] for item in load_json_safe(y).unwrap()]
                return [
                    Reason(f"No reference to `Instance.category_token`: {ins['category_token']}")
                    for ins in instance
                    if ins["category_token"] not in category_tokens
                ]
            case _:
                return [Reason("Missing `Instance` or `Category` file")]
