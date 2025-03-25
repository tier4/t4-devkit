from __future__ import annotations

from attrs import define, field, validators

__all__ = ["SemanticLabel"]


@define(frozen=True, eq=False)
class SemanticLabel:
    """A dataclass to represent semantic labels.

    Attributes:
        name (str): Label name.
        attributes (list[str], optional): List of attribute names.
    """

    name: str = field(validator=validators.instance_of(str))
    attributes: list[str] = field(
        factory=list,
        validator=validators.deep_iterable(validators.instance_of(str)),
    )

    def __eq__(self, other: str | SemanticLabel) -> bool:
        return self.name == other if isinstance(other, str) else self.name == other.name
