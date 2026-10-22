from __future__ import annotations

from enum import Enum, unique
from typing import Any

from attrs import converters, define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .annotation_type import AnnotationType

__all__ = ["ScenarioStatus", "Taxonomy", "Scenario"]


@unique
class ScenarioStatus(str, Enum):
    """Whether a scenario is selected or excluded."""

    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"


@define
class Taxonomy:
    """The vocabulary a scenario is tagged with.

    Attributes:
        id (str): Taxonomy ID, e.g. "cod-scene".
        version (str): Taxonomy version, e.g. "0.1.1".
    """

    id: str = field(validator=validators.instance_of(str))
    version: str = field(validator=validators.instance_of(str))


@define(slots=False)
class Scenario(SchemaBase):
    """`scenario.json` dataclass.

    A tagged time interval, e.g. from CodSceneClassifier.

    Attributes:
        token (str): Unique record identifier.
        log_token (str): Foreign key pointing to the log.
        start_timestamp (int): Start, Unix time stamp [us] (inclusive).
        end_timestamp (int): End, Unix time stamp [us] (exclusive).
        key_timestamp (int | None): Key moment [us].
        status (ScenarioStatus | None): Whether the scenario is selected or excluded.
        lateral_decision (str | None): Lateral decision, in the taxonomy's vocabulary.
        longitudinal_decision (str | None): Longitudinal decision, in the taxonomy's vocabulary.
        events (list[str]): Events, in the taxonomy's vocabulary.
        scenery (dict[str, Any] | None): Scenery, kept as given by the classifier.
        dynamic_entities (dict[str, Any] | None): Dynamic entities, kept as given.
        justification (str | None): Justification of the tags.
        taxonomy (Taxonomy): The vocabulary the scenario is tagged with.
        annotation_type (AnnotationType): How the label was made.
        provenance (str | None): Vendor, model name and version, or tool.
        confidence (float | None): Confidence in [0, 1], or None for manual labels.
        raw (dict[str, Any] | None): Original record.
    """

    log_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    start_timestamp: int = field(validator=validators.instance_of(int))
    end_timestamp: int = field(validator=validators.instance_of(int))
    key_timestamp: int | None = field(validator=validators.optional(validators.instance_of(int)))
    status: ScenarioStatus | None = field(converter=converters.optional(ScenarioStatus))
    lateral_decision: str | None = field(validator=validators.optional(validators.instance_of(str)))
    longitudinal_decision: str | None = field(
        validator=validators.optional(validators.instance_of(str))
    )
    events: list[str] = field(
        validator=validators.deep_iterable(
            validators.instance_of(str), validators.instance_of(list)
        )
    )
    scenery: dict[str, Any] | None = field(
        validator=validators.optional(validators.instance_of(dict))
    )
    dynamic_entities: dict[str, Any] | None = field(
        validator=validators.optional(validators.instance_of(dict))
    )
    justification: str | None = field(validator=validators.optional(validators.instance_of(str)))
    taxonomy: Taxonomy = field(
        converter=lambda x: Taxonomy(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(Taxonomy),
    )
    annotation_type: AnnotationType = field(converter=AnnotationType)
    provenance: str | None = field(validator=validators.optional(validators.instance_of(str)))
    confidence: float | None = field(
        validator=validators.optional(
            validators.and_(
                validators.instance_of((int, float)), validators.ge(0), validators.le(1)
            )
        )
    )
    raw: dict[str, Any] | None = field(validator=validators.optional(validators.instance_of(dict)))

    @end_timestamp.validator
    def _check_end_timestamp(self, attribute, value: int) -> None:
        if value < self.start_timestamp:
            raise ValueError(f"end_timestamp {value} is before start_timestamp")
