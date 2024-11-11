from __future__ import annotations

from attrs import define, field

__all__ = ["SemanticLabel"]


@define(frozen=True, eq=False)
class SemanticLabel:
    """A dataclass to represent semantic labels.

    Attributes:
        name (str): Label name.
        attributes (list[str], optional): List of attribute names.
    """

    name: str
    attributes: list[str] = field(factory=list)

    def __eq__(self, other: str | SemanticLabel) -> bool:
        return self.name == other if isinstance(other, str) else self.name == other.name
