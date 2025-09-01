from __future__ import annotations

from attrs import define, field, validators

__all__ = ["AutolabelModel"]


@define
class AutolabelModel:
    """A dataclass to represent a model used in autolabeling.

    Attributes:
        name (str): Name of the model used for annotation. Can include version information.
        score (float): Label score for the annotation from this model (range: 0.0–1.0).
        uncertainty (float | None, optional): Model-reported uncertainty for the annotation (range: 0.0–1.0). 
            Lower values imply higher confidence.
    """

    name: str = field(validator=validators.instance_of(str))
    score: float = field(
        validator=[
            validators.instance_of(float),
            validators.and_(validators.ge(0.0), validators.le(1.0))
        ]
    )
    uncertainty: float | None = field(
        default=None,
        validator=validators.optional([
            validators.instance_of(float),
            validators.and_(validators.ge(0.0), validators.le(1.0))
        ])
    )
