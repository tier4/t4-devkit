from __future__ import annotations

from attrs import define

from ..name import SchemaName
from .base import SchemaBase
from .registry import SCHEMAS

__all__ = ["Map"]


@define(slots=False)
@SCHEMAS.register(SchemaName.MAP)
class Map(SchemaBase):
    """A dataclass to represent schema table of `map.json`.

    Attributes:
        token (str): Unique record identifier.
        log_tokens (str): Foreign keys pointing the log tokens.
        category (str): Map category.
        filename (str): Relative path to the file with the map mask.
    """

    log_tokens: list[str]
    category: str
    filename: str
