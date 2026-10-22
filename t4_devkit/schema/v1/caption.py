from __future__ import annotations

from enum import Enum, unique

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .annotation_type import AnnotationType
from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["CaptionType", "Caption"]


@unique
class CaptionType(str, Enum):
    """Kind of caption text.

    Attributes:
        DESCRIPTION: Describes what happens in the window.
        REASONING: Explains why the ego vehicle or others act as they do.
        INSTRUCTION: An instruction to the ego vehicle.
        QUESTION_ANSWER: A question about the window and its answer.
    """

    DESCRIPTION = "description"
    REASONING = "reasoning"
    INSTRUCTION = "instruction"
    QUESTION_ANSWER = "question_answer"


@define(slots=False)
@SCHEMAS.register(SchemaName.CAPTION)
class Caption(SchemaBase):
    """`caption.json` dataclass.

    Natural-language text about a time window, for VLM/VLA training.

    Attributes:
        token (str): Unique record identifier.
        log_token (str): Foreign key pointing to the log.
        start_timestamp (int): Start of the window, Unix time stamp [us].
        end_timestamp (int): End of the window [us]. Equal to `start_timestamp` for one moment.
        sample_data_token (str | None): Foreign key pointing to the sample data the caption
            describes, if it is about one image or sweep.
        scenario_token (str | None): Foreign key pointing to a scenario.
        instance_tokens (list[str] | None): Foreign keys pointing to the instances the text
            refers to.
        caption_type (CaptionType): Kind of text.
        text (str): The text.
        language (str): Language code, e.g. "en", "ja".
        annotation_type (AnnotationType): How the label was made.
        provenance (str | None): VLM name and version, prompt ID, annotator or vendor.
        confidence (float | None): Confidence in [0, 1], or None for manual labels.
    """

    log_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    start_timestamp: int = field(validator=validators.instance_of(int))
    end_timestamp: int = field(validator=validators.instance_of(int))
    sample_data_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    scenario_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    instance_tokens: list[str] | None = field(
        validator=validators.optional(
            validators.deep_iterable(
                validators.and_(validators.instance_of(str), impossible_empty()),
                validators.instance_of(list),
            )
        )
    )
    caption_type: CaptionType = field(converter=CaptionType)
    text: str = field(validator=(validators.instance_of(str), impossible_empty()))
    language: str = field(validator=(validators.instance_of(str), impossible_empty()))
    annotation_type: AnnotationType = field(converter=AnnotationType)
    provenance: str | None = field(validator=validators.optional(validators.instance_of(str)))
    confidence: float | None = field(
        validator=validators.optional(
            validators.and_(
                validators.instance_of((int, float)), validators.ge(0), validators.le(1)
            )
        )
    )

    @end_timestamp.validator
    def _check_end_timestamp(self, attribute, value: int) -> None:
        if value < self.start_timestamp:
            raise ValueError(f"end_timestamp {value} is before start_timestamp")
