from __future__ import annotations

from attrs import define, field, validators

__all__ = ["AutolabelModel", "AutolabelMixin"]


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
            validators.and_(validators.ge(0.0), validators.le(1.0)),
        ]
    )
    uncertainty: float | None = field(
        default=None,
        validator=validators.optional(
            (validators.instance_of(float), validators.and_(validators.ge(0.0), validators.le(1.0)))
        ),
    )

    @staticmethod
    def to_autolabel_model(x) -> list[AutolabelModel] | None:
        """Convert input to a list of AutolabelModel instances.

        Args:
            x: Input to convert. Can be None, a list of dicts, or a list of AutolabelModel instances.

        Returns:
            list[AutolabelModel] | None: Converted list of AutolabelModel instances or None.
        """
        if x is None:
            return None
        if isinstance(x, list):
            return [AutolabelModel(**model) if isinstance(model, dict) else model for model in x]
        raise TypeError("Input must be None or a list of [dicts or AutolabelModel] instances.")


@define(slots=False)
class AutolabelMixin:
    """Mixin class for schema tables that use autolabel metadata with automatic annotation."""

    automatic_annotation: bool = field(
        default=False, validator=validators.instance_of(bool), kw_only=True
    )
    autolabel_metadata: list[AutolabelModel] | None = field(
        default=None,
        converter=AutolabelModel.to_autolabel_model,
        validator=validators.optional(
            validators.deep_iterable(validators.instance_of(AutolabelModel))
        ),
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        """Post-initialization validation for autolabel consistency."""
        # if automatic_annotation=True, autolabel_metadata must exist
        if self.automatic_annotation and self.autolabel_metadata is None:
            raise TypeError("autolabel_metadata must be provided when automatic_annotation is True")
        # if automatic_annotation=False, autolabel_metadata must not exist
        if not self.automatic_annotation and self.autolabel_metadata is not None:
            raise TypeError("autolabel_metadata must be None when automatic_annotation is False")
