from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from .base import Checker
from .result import GroupName, Report, TargetName, make_error, make_ok

if TYPE_CHECKING:
    from t4_devkit import Tier4


class RecordCountChecker(Checker):
    group = GroupName("record-count")

    @abstractmethod
    def __call__(self, t4: Tier4) -> list[Report]:
        pass


class SceneCountChecker(RecordCountChecker):
    target = TargetName("scene")

    def __call__(self, t4: Tier4) -> list[Report]:
        return self._check_scene_count(t4)

    def _check_scene_count(self, t4: Tier4) -> list[Report]:
        rule = "scene-is-one"
        if t4.scene != 1:
            return [make_error(rule, "The number of scene records is not 1")]
        else:
            return [make_ok(rule)]


class SampleCountChecker(RecordCountChecker):
    target = TargetName("sample")

    def __call__(self, t4: Tier4) -> list[Report]:
        reports = []
        reports.extend(self._check_sample_count(t4))
        reports.extend(self._check_next_prev_token_count(t4))
        return reports

    def _check_sample_count(self, t4: Tier4) -> list[Report]:
        rule = "sample-is-not-zero"
        if t4.sample == 0:
            return [make_error(rule, "The number of sample records is 0")]
        else:
            return [make_ok(rule)]

    def _check_next_prev_token_count(self, t4: Tier4) -> list[Report]:
        no_next_token_count = 0
        no_prev_token_count = 0

        for sample in t4.sample:
            if sample.next == "":
                no_next_token_count += 1
            if sample.prev == "":
                no_prev_token_count += 1

        reports = []
        no_next_rule = "no-next-is-same-as-scene-number"

        if no_next_token_count != len(t4.scene):
            reports.append(
                make_error(
                    no_next_rule,
                    "Sample records must have the same number of empty next tokens as the number of scene records",
                )
            )
        else:
            reports.append(make_ok(no_next_rule))

        no_prev_rule = "no-prev-is-same-as-scene-number"
        if no_prev_token_count != len(t4.scene):
            reports.append(
                make_error(
                    no_prev_rule,
                    "Sample records must have the same number of empty prev tokens as the number of scene records",
                )
            )
        else:
            reports.append(make_ok(no_prev_rule))

        return reports
