from __future__ import annotations

from enum import Enum, unique

from attrs import define, field, validators

from t4_devkit.common.converter import to_quaternion
from t4_devkit.schema.tables.base import SchemaBase, impossible_empty
from t4_devkit.typing import Quaternion, Vector3

__all__ = ["RouteSource", "RoutePose", "RouteSegment", "Route"]


@unique
class RouteSource(str, Enum):
    """Where a route came from."""

    MISSION_PLANNER = "mission_planner"
    MANUAL = "manual"
    DERIVED = "derived"


@define
class RoutePose:
    """A route start or goal pose in the map frame, as in LaneletRoute.

    Attributes:
        translation (Vector3): Position [x, y, z] in [m].
        rotation (Quaternion): Orientation as quaternion [w, x, y, z].
    """

    translation: Vector3 = field(converter=Vector3)
    rotation: Quaternion = field(converter=to_quaternion)


@define
class RouteSegment:
    """A route segment, as in Autoware LaneletSegment.

    Attributes:
        preferred_primitive_id (int): Preferred lanelet ID.
        primitive_ids (list[int]): All lanelet IDs of the segment.
    """

    preferred_primitive_id: int = field(validator=validators.instance_of(int))
    primitive_ids: list[int] = field(
        validator=validators.deep_iterable(
            validators.instance_of(int), validators.instance_of(list)
        )
    )


@define(slots=False)
class Route(SchemaBase):
    """`route.json` dataclass.

    The mission route, from Autoware LaneletRoute. A re-route adds a new row.

    Attributes:
        token (str): Unique record identifier.
        log_token (str): Foreign key pointing to the log.
        map_token (str): Foreign key pointing to the map.
        valid_from (int): Start of validity, Unix time stamp [us] (inclusive).
        valid_until (int | None): End of validity [us] (exclusive), or None until the end.
        route_uuid (str | None): `LaneletRoute.uuid`.
        start_pose (RoutePose): Start pose in the map frame.
        goal_pose (RoutePose): Goal pose in the map frame.
        segments (list[RouteSegment]): Route segments, in order.
        allow_modification (bool | None): `LaneletRoute.allow_modification`.
        source (RouteSource): Where the route came from.
        provenance (str | None): Where the message was found, e.g. "own_bag", "route_json".
    """

    log_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    map_token: str = field(validator=(validators.instance_of(str), impossible_empty()))
    valid_from: int = field(validator=validators.instance_of(int))
    valid_until: int | None = field(validator=validators.optional(validators.instance_of(int)))
    route_uuid: str | None = field(validator=validators.optional(validators.instance_of(str)))
    start_pose: RoutePose = field(
        converter=lambda x: RoutePose(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(RoutePose),
    )
    goal_pose: RoutePose = field(
        converter=lambda x: RoutePose(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(RoutePose),
    )
    segments: list[RouteSegment] = field(
        converter=lambda x: [RouteSegment(**v) if isinstance(v, dict) else v for v in x],
        validator=validators.deep_iterable(
            validators.instance_of(RouteSegment), validators.instance_of(list)
        ),
    )
    allow_modification: bool | None = field(
        validator=validators.optional(validators.instance_of(bool))
    )
    source: RouteSource = field(converter=RouteSource)
    provenance: str | None = field(validator=validators.optional(validators.instance_of(str)))
