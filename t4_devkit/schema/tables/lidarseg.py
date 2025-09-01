from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ["Lidarseg"]


@define(slots=False)
@SCHEMAS.register(SchemaName.LIDARSEG)
class Lidarseg(SchemaBase):
    """A dataclass to represent schema table of `lidarseg.json`.

    Attributes:
        token (str): Unique record identifier.
        sample_data_token (str): Foreign key pointing to the sample data, which must be a keyframe image.
        filename (str): The name of the .bin files containing the lidarseg labels. These are numpy arrays of uint8 stored in binary format using numpy.

    Shortcuts:
    ---------
        (None currently defined)
    """

    sample_data_token: str = field(validator=validators.instance_of(str))
    filename: str = field(validator=validators.instance_of(str))
