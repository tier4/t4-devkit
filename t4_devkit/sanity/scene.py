from __future__ import annotations

from typing import TYPE_CHECKING

from returns.pipeline import is_successful

from .result import CheckerName, GroupName, Report, make_error, make_ok
from .utility import lookup_table

if TYPE_CHECKING:
    from t4_devkit import Tier4


class SceneFormatChecker:
    @property
    def group(self) -> GroupName:
        return GroupName("Scene")

    @property
    def name(self) -> CheckerName:
        return CheckerName("SceneFormatChecker")

    def __call__(self, annotation_dir: str) -> list[Report]:
        pass


class SceneNumberChecker:
    @property
    def group(self) -> GroupName:
        return GroupName("Scene")

    @property
    def name(self) -> CheckerName:
        return CheckerName("SceneNumberChecker")

    def __call__(self, t4: Tier4) -> list[Report]:
        if len(t4.scene) != 1:
            return [make_error(self.name, "Scene number is not 1")]
        else:
            return [make_ok(self.name)]


class SceneRelationChecker:
    @property
    def group(self) -> GroupName:
        return GroupName("Scene")

    @property
    def name(self) -> CheckerName:
        return CheckerName("SceneRelationChecker")

    def __call__(self, t4: Tier4) -> list[Report]:
        reports = []
        scene = t4.scene[0]

        if not is_successful(lookup_table(t4, "log", scene.log_token)):
            reports.append(make_error(self.name, f"Log not found for {scene.log_token=}"))

        if not is_successful(lookup_table(t4, "sample", scene.first_sample_token)):
            reports.append(
                make_error(self.name, f"Sample token not found for {scene.first_sample_token=}")
            )

        if not is_successful(lookup_table(t4, "sample", scene.last_sample_token)):
            reports.append(
                make_error(self.name, f"Sample token not found for {scene.last_sample_token=}")
            )

        return reports if len(reports) > 0 else [make_ok(self.name)]
