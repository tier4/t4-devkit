from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from returns.pipeline import is_successful
from returns.result import Result, safe

from .base import Checker
from .result import GroupName, Report, TargetName, make_error, make_ok

if TYPE_CHECKING:
    from t4_devkit import Tier4
    from t4_devkit.schema import SchemaTable


def lookup_table(self, t4: Tier4, table_name: str, token: str, rule: str) -> Report:
    @safe
    def _try_lookup_table(t4: Tier4, table_name: str, token: str) -> Result[SchemaTable, Exception]:
        return t4.get(table_name, token)

    if is_successful(_try_lookup_table(t4, table_name, token)):
        return make_ok(rule)
    else:
        return make_error(rule, f"'{table_name}' not found for {token=}")


class RelationChecker(Checker):
    group = GroupName("relation")

    @abstractmethod
    def __call__(self, t4: Tier4) -> list[Report]:
        pass


class SceneRelationChecker(RelationChecker):
    target = TargetName("scene")

    def __call__(self, t4: Tier4) -> list[Report]:
        reports = []
        scene = t4.scene[0]
        reports += lookup_table(t4, "log", scene.token, "scene-to-log")
        reports += lookup_table(t4, "sample", scene.first_sample_token, "scene-to-first-sample")
        reports += lookup_table(t4, "sample", scene.last_sample_token, "scene-to-last-sample")


class SampleRelationChecker(RelationChecker):
    target = TargetName("sample")

    def __call__(self, t4: Tier4) -> list[Report]:
        reports = []
        no_next_token_count: int = 0
        no_prev_token_count: int = 0
        for sample in t4.sample:
            if sample.next == "":
                no_next_token_count += 1
            else:
                reports += lookup_table(t4, "sample", sample.next_token, "sample-to-next")

            if sample.prev == "":
                no_prev_token_count += 1
            else:
                reports += lookup_table(t4, "sample", sample.prev_token, "sample-to-prev")

        no_next_rule = "no-next-sample-is-same-as-scene"
        if no_next_token_count != len(t4.scene):
            reports.append(
                make_error(
                    no_next_rule,
                    "The number of samples without a next token is not equal to the number of scenes",
                )
            )
        else:
            reports.append(make_ok(no_next_rule))

        no_prev_rule = "no-prev-sample-is-same-as-scene"
        if no_prev_token_count != len(t4.scene):
            reports.append(
                make_error(
                    no_prev_rule,
                    "The number of samples without a prev token is not equal to the number of scenes",
                )
            )
        else:
            reports.append(make_ok(no_prev_rule))

        return reports
