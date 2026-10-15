from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["Scene"]


@define(slots=False)
@SCHEMAS.register(SchemaName.SCENE)
class Scene(SchemaBase):
    """`scene.json` dataclass.

    Attributes:
        token (str): Unique record identifier.
        name (str): Short string identifier.
        description (str | None): Longer description of the scene.
        log_token (str): Foreign key pointing to the log the scene was extracted from.
        nbr_samples (int): Number of samples in the scene.
        first_sample_token (str): Foreign key pointing to the first sample in the scene.
        last_sample_token (str): Foreign key pointing to the last sample in the scene.
    """

    name: str = field(validator=validators.instance_of(str))
    description: str | None = field(validator=validators.optional(validators.instance_of(str)))
    log_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    nbr_samples: int = field(validator=(validators.instance_of(int), validators.ge(0)))
    first_sample_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    last_sample_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
