from __future__ import annotations

from attrs import converters, define, field, validators

from t4_devkit.common.converter import to_quaternion
from t4_devkit.schema.tables.base import SchemaBase, impossible_empty
from t4_devkit.typing import Quaternion, Vector3

from .annotation_type import AnnotationType
from .name import SchemaName
from .registry import SCHEMAS

__all__ = ["SampleAnnotation"]


@define(slots=False)
@SCHEMAS.register(SchemaName.SAMPLE_ANNOTATION)
class SampleAnnotation(SchemaBase):
    """`sample_annotation.json` dataclass.

    A 3D box in the map frame.

    Attributes:
        token (str): Unique record identifier.
        sample_token (str): Foreign key pointing to the sample.
        instance_token (str): Foreign key pointing to the instance.
        attribute_tokens (list[str]): Foreign keys pointing to the attributes.
        visibility_token (str): Foreign key pointing to the visibility level.
        translation (Vector3): Box center [x, y, z] in [m].
        size (Vector3): Box size [width, length, height] in [m].
        rotation (Quaternion): Box orientation as quaternion [w, x, y, z].
        velocity (Vector3 | None): Velocity [vx, vy, vz] in [m/s].
        acceleration (Vector3 | None): Acceleration [ax, ay, az] in [m/s^2].
        num_lidar_pts (int | None): Number of LiDAR points in the box, or None if not counted.
        num_radar_pts (int | None): Number of radar points in the box, or None if not counted.
        next (str | None): Foreign key pointing to the next annotation of the instance.
        prev (str | None): Foreign key pointing to the previous annotation of the instance.
        annotation_type (AnnotationType): How the label was made.
        provenance (str | None): Vendor, model name and version, or tool.
        confidence (float | None): Confidence in [0, 1], or None for manual labels.
    """

    sample_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    instance_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    attribute_tokens: list[str] = field(
        validator=validators.deep_iterable(
            validators.and_(validators.instance_of(str), impossible_empty()),
            validators.instance_of(list),
        )
    )
    visibility_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    translation: Vector3 = field(converter=Vector3)
    size: Vector3 = field(converter=Vector3)
    rotation: Quaternion = field(converter=to_quaternion)
    velocity: Vector3 | None = field(converter=converters.optional(Vector3))
    acceleration: Vector3 | None = field(converter=converters.optional(Vector3))
    num_lidar_pts: int | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(int), validators.ge(0))
        )
    )
    num_radar_pts: int | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(int), validators.ge(0))
        )
    )
    next: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    prev: str | None = field(
        validator=validators.optional(
            validators.and_(validators.instance_of(str), impossible_empty())
        )
    )
    annotation_type: AnnotationType = field(converter=AnnotationType)
    provenance: str | None = field(validator=validators.optional(validators.instance_of(str)))
    confidence: float | None = field(
        validator=validators.optional(
            validators.and_(
                validators.instance_of((int, float)), validators.ge(0), validators.le(1)
            )
        )
    )
