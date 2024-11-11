from __future__ import annotations

from attrs import define

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ["Scene"]


@define(slots=False)
@SCHEMAS.register(SchemaName.SCENE)
class Scene(SchemaBase):
    """A dataclass to represent schema table of `scene.json`.

    Attributes:
        token (str): Unique record identifier.
        name (str): Short string identifier.
        description (str): Longer description for the scene.
        log_token (str): Foreign key pointing to log from where the data was extracted.
        nbr_samples (int): Number of samples in the scene.
        first_sample_token (str): Foreign key pointing to the first sample in scene.
        last_sample_token (str): Foreign key pointing to the last sample in scene.
    """

    name: str
    description: str
    log_token: str
    nbr_samples: int
    first_sample_token: str
    last_sample_token: str
