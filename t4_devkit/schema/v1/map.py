from __future__ import annotations

from enum import Enum, unique

from attrs import converters, define, field, validators

from t4_devkit.schema.tables.base import SchemaBase, impossible_empty

__all__ = ["MapFormat", "ProjectorType", "MapSource", "ProjectorOrigin", "Projector", "Map"]


@unique
class MapFormat(str, Enum):
    """File format of a map."""

    LANELET2_OSM = "lanelet2_osm"


@unique
class ProjectorType(str, Enum):
    """Map projection, as in Autoware's map_projector_info."""

    MGRS = "MGRS"
    TRANSVERSE_MERCATOR = "TransverseMercator"
    LOCAL_CARTESIAN_UTM = "LocalCartesianUTM"


@unique
class MapSource(str, Enum):
    """Where a map came from."""

    WEBAUTO = "webauto"
    MANUAL = "manual"


@define
class ProjectorOrigin:
    """Origin of the map projection.

    Attributes:
        lat (float | None): Latitude [deg].
        lon (float | None): Longitude [deg].
        alt (float | None): Altitude [m].
    """

    lat: float | None = field(validator=validators.optional(validators.instance_of((int, float))))
    lon: float | None = field(validator=validators.optional(validators.instance_of((int, float))))
    alt: float | None = field(validator=validators.optional(validators.instance_of((int, float))))


@define
class Projector:
    """Map projection.

    Attributes:
        type (ProjectorType | None): Projection type.
        mgrs_grid (str | None): MGRS grid.
        origin (ProjectorOrigin): Projection origin.
    """

    type: ProjectorType | None = field(converter=converters.optional(ProjectorType))
    mgrs_grid: str | None = field(validator=validators.optional(validators.instance_of(str)))
    origin: ProjectorOrigin = field(
        converter=lambda x: ProjectorOrigin(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(ProjectorOrigin),
    )


@define(slots=False)
class Map(SchemaBase):
    """`map.json` dataclass.

    Lane data stays in the lanelet2 file; this table holds the map identity.

    Attributes:
        token (str): Unique record identifier.
        log_tokens (list[str]): Foreign keys pointing to the logs.
        format (MapFormat): Map file format.
        filename (str): Path to the map file.
        sha256 (str): SHA-256 of the map file.
        map_id (str): Web.Auto area map ID.
        version_id (str): Web.Auto area map version ID.
        projector (Projector): Map projection.
        source (MapSource): Where the map came from.
        name (str | None): Map name.
    """

    log_tokens: list[str] = field(
        validator=validators.deep_iterable(
            (validators.instance_of(str), impossible_empty()), validators.instance_of(list)
        )
    )
    format: MapFormat = field(converter=MapFormat)
    filename: str = field(validator=validators.instance_of(str))
    sha256: str = field(validator=validators.matches_re(r"^[0-9a-f]{64}$"))
    map_id: str = field(validator=validators.instance_of(str))
    version_id: str = field(validator=validators.instance_of(str))
    projector: Projector = field(
        converter=lambda x: Projector(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(Projector),
    )
    source: MapSource = field(converter=MapSource)
    name: str | None = field(validator=validators.optional(validators.instance_of(str)))
