from __future__ import annotations

import warnings
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Callable

from attrs import define, field
from returns.pipeline import flow, is_successful
from returns.result import Result, safe

from t4_devkit import Tier4

if TYPE_CHECKING:
    from t4_devkit.schema import SchemaTable


class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    WARNING = "WARNING"


@define
class Report:
    status: Status
    message: str | None = None


@define
class SanityResult:
    dataset_id: str
    version: str | None
    reports: dict[str, list[Report]] = field(factory=lambda: defaultdict(list))

    def add_report(self, checker: Callable[[Tier4], list[Report]], t4: Tier4):
        self.reports[checker.__name__].extend(checker(t4))


def sanity_check(
    db_root: str,
    revision: str | None = None,
    *,
    include_warning: bool = False,
) -> SanityResult:
    with warnings.catch_warnings():
        if include_warning:
            warnings.filterwarnings("error")
        else:
            warnings.filterwarnings("ignore")

        t4_result = _try_tier4(db_root, revision=revision)

        if not is_successful(t4_result):
            raise ValueError("Failed to load Tier4")

        t4 = t4_result.unwrap()

        result = SanityResult(dataset_id=t4.dataset_id, version=t4.version)

        result.add_report(_check_scene, t4)
        result.add_report(_check_sample, t4)

    return t4


def _try_tier4(data_root: str, revision: str | None = None) -> Result[Tier4, Exception]:
    """Try to load Tier4 data from the given root directory.

    Args:
        data_root: The root directory of the Tier4 data.
        revision: The revision of the Tier4 data to load.

    Returns:
        A Result object containing the loaded Tier4 data or an exception.
    """

    @safe
    def _load_t4_safe(data_root: str):
        return Tier4(data_root, revision=revision, verbose=False)

    return flow(data_root, _load_t4_safe)


@safe
def _find_in_table(t4: Tier4, table_name: str, token: str) -> Result[SchemaTable, Exception]:
    return t4.get(table_name, token)


def _check_scene(t4: Tier4) -> list[Report]:
    if len(t4.scene) != 1:
        return [Report(Status.ERROR, "The number of scenes is not 1")]

    scene = t4.scene[0]
    if not is_successful(_find_in_table(t4, "log", scene.log_token)):
        return [Report(Status.ERROR, "scene.log_token isn't found in log")]

    if not is_successful(_find_in_table(t4, "sample", scene.first_sample_token)):
        return [Report(Status.ERROR, "scene.first_sample_token isn't found in sample")]

    if not is_successful(_find_in_table(t4, "sample", scene.last_sample_token)):
        return [Report(Status.ERROR, "scene.last_sample_token isn't found in sample")]

    return [Report(Status.OK)]


def _check_sample(t4: Tier4) -> list[Report]:
    reports = []
    if not len(t4.sample) > 0:
        reports.append(Report(Status.ERROR, "The number of samples is not greater than 0"))

    no_next_token_count: int = 0
    no_prev_token_count: int = 0
    for sample in t4.sample:
        if not is_successful(_find_in_table(t4, "scene", sample.scene_token)):
            reports.append(Report(Status.ERROR, "sample.scene_token isn't found in scene"))
        next_token = sample.next
        if next_token == "":
            no_next_token_count += 1
        else:
            if not is_successful(_find_in_table(t4, "sample", next_token)):
                reports.append(Report(Status.ERROR, "sample.next isn't found in sample"))

        prev_token = sample.prev
        if prev_token == "":
            no_prev_token_count += 1
        else:
            if not is_successful(_find_in_table(t4, "sample", prev_token)):
                reports.append(Report(Status.ERROR, "sample.prev isn't found in sample"))

    if no_next_token_count != len(t4.scene):
        reports.append(
            Report(
                Status.ERROR,
                "The number of samples with no next token is not equal to the number of scenes",
            )
        )
    if no_prev_token_count != len(t4.scene):
        reports.append(
            Report(
                Status.ERROR,
                "The number of samples with no previous token is not equal to the number of scenes",
            )
        )
    return reports if len(reports) == 0 else [Report(Status.OK)]


def _check_sample_data(t4: Tier4) -> list[Report]:
    reports: list[Report] = []
    if not len(t4.sample_data) > 0:
        reports.append(Report(Status.ERROR, "The number of samples is not greater than 0"))

    no_next_token_count: int = 0
    no_prev_token_count: int = 0
    for sample_data in t4.sample_data:
        if not sample_data.is_valid:
            reports.append(Report(Status.WARNING, "sample_data is not valid"))
            continue
        if not is_successful(_find_in_table(t4, "sample", sample_data.sample_token)):
            reports.append(Report(Status.ERROR, "sample_data.sample_token isn't found in sample"))
        if not is_successful(_find_in_table(t4, "ego_pose", sample_data.ego_pose_token)):
            reports.append(
                Report(Status.ERROR, "sample_data.ego_pose_token isn't found in ego_pose")
            )
