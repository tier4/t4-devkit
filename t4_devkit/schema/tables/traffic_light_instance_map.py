from __future__ import annotations

from attrs import define, field, validators

from ..name import SchemaName
from .base import SchemaBase, impossible_empty
from .registry import SCHEMAS

__all__ = ["TrafficLightInstanceMap"]


@define(slots=False)
@SCHEMAS.register(SchemaName.TRAFFIC_LIGHT_INSTANCE_MAP)
class TrafficLightInstanceMap(SchemaBase):
    """A dataclass to represent schema table of `traffic_light_instance_map.json`.

    This table stores only the relation from a 2D physical traffic-light instance to the
    Lanelet2 LineString that represents its lamp geometry on the map:

        object_ann.instance_token -> instance.token (this table) -> traffic_light_linestring_id
            -> map Regulatory Element (resolved from the map, not stored here)

    It is *not* a per-frame traffic-light state table: signal color/shape state is read
    from `object_ann.category_token` / `object_ann.attribute_tokens`, and Regulatory
    Element / group relations are resolved by walking the Lanelet2 map's
    `regulatory_element` relations that refer to `traffic_light_linestring_id` (see
    `t4_devkit.lanelet.build_linestring_to_regulatory_element_index`). This keeps the
    relation record free of information that is redundant with, or could drift out of
    sync with, the map and other annotation tables.

    Deliberately not named `traffic_light.json` / `TrafficLight`: that name is reserved
    for a per-frame traffic-light lamp-state table (`{token, sample_token,
    lane_connector_id, elements}`); this table is a static instance-to-map relation
    instead and must not be confused with it.

    A dataset only has this table when the traffic-light-to-map relation is known
    (Tier B'); its absence means the dataset does not carry that identity (Tier B).

    Cardinality: one `instance_token` maps to at most one `traffic_light_linestring_id`.
    If a LineString is referred to by more than one Regulatory Element, that is an
    ambiguous relation and must be treated as a validation error rather than resolved
    implicitly (see `t4_devkit.lanelet.build_linestring_to_regulatory_element_index`).
    Multiple LineStrings/2D instances may point to the same Regulatory Element.

    Attributes:
        token (str): Unique record identifier.
        instance_token (str): Foreign key pointing to the 2D/physical traffic-light instance.
        traffic_light_linestring_id (str): ID of the Lanelet2 LineString representing the
            traffic light lamp on the map.
    """

    instance_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    traffic_light_linestring_id: str = field(
        validator=(validators.instance_of(str), impossible_empty())
    )
