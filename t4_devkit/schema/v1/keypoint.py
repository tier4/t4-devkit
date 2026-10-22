from __future__ import annotations

import numpy as np
from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .annotation_type import AnnotationType

__all__ = ["Keypoint"]


@define(slots=False)
class Keypoint(SchemaBase):
    """`keypoint.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        sample_data_token (str): Foreign key pointing to the sample data.
        instance_token (str): Foreign key pointing to the instance.
        category_tokens (list[str]): Foreign keys pointing to the category of each keypoint.
        keypoints (np.ndarray): Keypoints in shape (N, 2), as (x, y) in pixels.
        num_keypoints (int): Number of keypoints.
        annotation_type (AnnotationType): How the label was made.
        provenance (str | None): Vendor, model name and version, or tool.
        confidence (float | None): Confidence in [0, 1], or None for manual labels.
    """

    sample_data_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    instance_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    category_tokens: list[str] = field(
        validator=validators.deep_iterable(
            validators.and_(validators.instance_of(str), impossible_empty()),
            validators.instance_of(list),
        )
    )
    keypoints: np.ndarray = field(converter=np.array)
    num_keypoints: int = field(validator=(validators.instance_of(int), validators.ge(0)))
    annotation_type: AnnotationType = field(converter=AnnotationType)
    provenance: str | None = field(validator=validators.optional(validators.instance_of(str)))
    confidence: float | None = field(
        validator=validators.optional(
            validators.and_(
                validators.instance_of((int, float)), validators.ge(0), validators.le(1)
            )
        )
    )

    @keypoints.validator
    def _check_keypoints(self, attribute, value: np.ndarray) -> None:
        if value.ndim != 2 or value.shape[1] != 2:
            raise ValueError(f"keypoints must have shape (N, 2), got {value.shape}")
