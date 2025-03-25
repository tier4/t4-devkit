from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

if TYPE_CHECKING:
    from t4_devkit.typing import KeypointLike

__all__ = ["Keypoint"]


@define(slots=False)
@SCHEMAS.register(SchemaName.KEYPOINT)
class Keypoint(SchemaBase):
    """A dataclass to represent schema table of `keypoint.json`.

    Attributes:
        token (str): Unique record identifier.
        sample_data_token (str): Foreign key pointing to the sample data, which must be a keyframe image.
        instance_token (str): Foreign key pointing to the instance.
        category_tokens (list[str]): Foreign key pointing to keypoints categories.
        keypoints (KeypointLike): Annotated keypoints. Given as a list of [x, y].
        num_keypoints (int): The number of keypoints to be annotated.
    """

    sample_data_token: str = field(validator=validators.instance_of(str))
    instance_token: str = field(validator=validators.instance_of(str))
    category_tokens: list[str] = field(
        validator=validators.deep_iterable(validators.instance_of(str))
    )
    keypoints: KeypointLike = field(converter=np.array)
    num_keypoints: int = field(validator=validators.instance_of(int))
