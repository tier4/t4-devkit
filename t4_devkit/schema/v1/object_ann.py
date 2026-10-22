from __future__ import annotations

from attrs import define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty
from t4_devkit.schema.tables.object_ann import RLEMask

from .annotation_type import AnnotationType
from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["ObjectAnn"]


@define(slots=False)
@SCHEMAS.register(SchemaName.OBJECT_ANN)
class ObjectAnn(SchemaBase):
    """`object_ann.json` dataclass.

    A 2D annotation in an image: a box with an optional mask. For categories with `is_thing`,
    the mask is an instance mask and `instance_token` is set; for other categories (road, sky),
    it is a semantic mask and `instance_token` is None. Replaces `object_ann` and `surface_ann`
    of 0.x.

    Attributes:
        token (str): Unique record identifier.
        sample_data_token (str): Foreign key pointing to the sample data.
        instance_token (str | None): Foreign key pointing to the instance, or None for categories
            without `is_thing`.
        category_token (str): Foreign key pointing to the category.
        attribute_tokens (list[str]): Foreign keys pointing to the attributes.
        bbox (tuple[float, float, float, float]): (xmin, ymin, xmax, ymax) in pixels.
        mask (RLEMask | None): Instance mask, or semantic mask for categories without `is_thing`.
        orientation (float | None): Arrow orientation [rad], for categories with `has_orientation`.
        number (int | None): Displayed digit, for categories with `has_number`.
        annotation_type (AnnotationType): How the label was made.
        provenance (str | None): Vendor, model name and version, or tool.
        confidence (float | None): Confidence in [0, 1], or None for manual labels.
    """

    sample_data_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    instance_token: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    category_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    attribute_tokens: list[str] = field(
        validator=validators.deep_iterable(
            validators.and_(validators.instance_of(str), impossible_empty()),
            validators.instance_of(list),
        )
    )
    bbox: tuple[float, float, float, float] = field(
        converter=tuple,
        validator=validators.deep_iterable(
            validators.instance_of((int, float)),
            validators.and_(validators.min_len(4), validators.max_len(4)),
        ),
    )
    mask: RLEMask | None = field(
        converter=lambda x: RLEMask(**x) if isinstance(x, dict) else x,
        validator=validators.optional(validators.instance_of(RLEMask)),
    )
    orientation: float | None = field(
        validator=validators.optional(validators.instance_of((int, float)))
    )
    number: int | None = field(validator=validators.optional(validators.instance_of(int)))
    annotation_type: AnnotationType = field(converter=AnnotationType)
    provenance: str | None = field(validator=validators.optional(validators.instance_of(str)))
    confidence: float | None = field(
        validator=validators.optional(
            validators.and_(
                validators.instance_of((int, float)), validators.ge(0), validators.le(1)
            )
        )
    )
