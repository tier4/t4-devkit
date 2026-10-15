from __future__ import annotations

import os.path as osp
from enum import Enum, unique
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from attrs import converters, define, field, validators

from t4_devkit.common.io import load_json
from t4_devkit.schema.tables.sensor import SensorModality

from .name import SchemaName

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = [
    "MANIFEST_FILENAME",
    "SUPPORTED_SCHEMA_MAJOR_VERSION",
    "Task",
    "RosbagStorage",
    "Generator",
    "Modalities",
    "Capabilities",
    "AnnotationSpecification",
    "TableEntry",
    "AssetEntry",
    "Rosbag",
    "Provenance",
    "Manifest",
    "load_manifest",
]

MANIFEST_FILENAME = "manifest.json"
SUPPORTED_SCHEMA_MAJOR_VERSION = 1


@unique
class Task(str, Enum):
    """Tasks a dataset can be used for."""

    DETECTION3D = "detection3d"
    DETECTION2D = "detection2d"
    SEGMENTATION2D = "segmentation2d"
    SEGMENTATION3D = "segmentation3d"
    KEYPOINT = "keypoint"
    TRAFFIC_LIGHT = "traffic_light"
    PREDICTION = "prediction"
    PLANNING = "planning"


@unique
class RosbagStorage(str, Enum):
    """Storage format of the source rosbag."""

    SQLITE3 = "sqlite3"
    MCAP = "mcap"
    OTHER = "other"


@define
class Generator:
    """A tool or library that produced the dataset.

    Attributes:
        name (str): Tool or library name.
        version (str): Version or commit hash.
    """

    name: str = field(validator=validators.instance_of(str))
    version: str = field(validator=validators.instance_of(str))


@define
class Modalities:
    """Sensor channel names per modality.

    Attributes:
        camera (list[str]): Camera channel names.
        lidar (list[str]): LiDAR channel names.
        radar (list[str]): Radar channel names.
    """

    camera: list[str] = field(
        validator=validators.deep_iterable(
            validators.instance_of(str), validators.instance_of(list)
        )
    )
    lidar: list[str] = field(
        validator=validators.deep_iterable(
            validators.instance_of(str), validators.instance_of(list)
        )
    )
    radar: list[str] = field(
        validator=validators.deep_iterable(
            validators.instance_of(str), validators.instance_of(list)
        )
    )


@define
class Capabilities:
    """What the dataset contains.

    Attributes:
        tasks (list[Task]): Tasks the dataset can be used for.
        modalities (Modalities): Sensor channel names per modality.
        map (bool): Whether a lanelet2 map is included.
        route (bool): Whether the `route` table is filled.
        traffic_light (bool): Whether the `traffic_light` table is filled.
        vehicle_state (bool): Whether the `vehicle_state` table is filled.
        scenario (bool): Whether the `scenario` table is filled.
    """

    tasks: list[Task] = field(converter=lambda values: [Task(v) for v in values])
    modalities: Modalities = field(
        converter=lambda x: Modalities(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(Modalities),
    )
    map: bool = field(validator=validators.instance_of(bool))
    route: bool = field(validator=validators.instance_of(bool))
    traffic_light: bool = field(validator=validators.instance_of(bool))
    vehicle_state: bool = field(validator=validators.instance_of(bool))
    scenario: bool = field(validator=validators.instance_of(bool))

    @classmethod
    def from_tables(cls, tables: Mapping[SchemaName, Sequence[Any]]) -> Capabilities:
        """Return what the tables contain: channels with frames, filled tables, tasks with labels.

        `prediction` needs every sample to have a key frame (all frames annotated); 
        `planning`needs scenarios.

        Args:
            tables (Mapping[SchemaName, Sequence[Any]]): 1.0 records per table; a missing table
                is empty.

        Returns:
            The capabilities.
        """

        def records(table: SchemaName) -> Sequence[Any]:
            return tables.get(table, [])

        sensors = records(SchemaName.SENSOR)
        with_frames = {frame.sensor_token for frame in records(SchemaName.SAMPLE_DATA)}
        channels = {
            modality: list(
                dict.fromkeys(
                    sensor.channel
                    for sensor in sensors
                    if sensor.modality == modality and sensor.token in with_frames
                )
            )
            for modality in SensorModality
        }
        lidar_columns = {
            field.name
            for sensor in sensors
            if sensor.lidar is not None
            for field in sensor.lidar.fields
        }
        samples = records(SchemaName.SAMPLE)
        things = {category.token for category in records(SchemaName.CATEGORY) if category.is_thing}
        object_anns = records(SchemaName.OBJECT_ANN)
        has_task = {
            Task.DETECTION3D: bool(records(SchemaName.SAMPLE_ANNOTATION)),
            Task.DETECTION2D: any(ann.category_token in things for ann in object_anns),
            Task.SEGMENTATION2D: any(ann.mask is not None for ann in object_anns),
            Task.SEGMENTATION3D: "label" in lidar_columns,
            Task.KEYPOINT: bool(records(SchemaName.KEYPOINT)),
            # states, or lamp instances linked to the map
            Task.TRAFFIC_LIGHT: bool(records(SchemaName.TRAFFIC_LIGHT))
            or any(
                instance.map_element.id is not None for instance in records(SchemaName.INSTANCE)
            ),
            Task.PREDICTION: bool(samples) and all(sample.has_key_frame for sample in samples),
            Task.PLANNING: bool(records(SchemaName.SCENARIO)),
        }
        return cls(
            tasks=[task for task in Task if has_task[task]],
            modalities=Modalities(
                camera=channels[SensorModality.CAMERA],
                lidar=channels[SensorModality.LIDAR],
                radar=channels[SensorModality.RADAR],
            ),
            map=bool(records(SchemaName.MAP)),
            route=bool(records(SchemaName.ROUTE)),
            traffic_light=bool(records(SchemaName.TRAFFIC_LIGHT)),
            vehicle_state=bool(records(SchemaName.VEHICLE_STATE)),
            scenario=bool(records(SchemaName.SCENARIO)),
        )


@define
class AnnotationSpecification:
    """Annotation specification of a task.

    Attributes:
        id (str): Annotation specification ID.
        version (str | None): Specification version, or None if unknown.
    """

    id: str = field(validator=validators.instance_of(str))
    version: str | None = field(validator=validators.optional(validators.instance_of(str)))


@define
class TableEntry:
    """A table file and its hash.

    Attributes:
        path (str): Path relative to the dataset root.
        sha256 (str): SHA-256 of the file.
    """

    path: str = field(validator=validators.instance_of(str))
    sha256: str = field(validator=validators.matches_re(r"^[0-9a-f]{64}$"))


@define
class AssetEntry:
    """A file asset, as in sensor, map or input bag file with its hash and size.

    Attributes:
        path (str): Path relative to the dataset root.
        sha256 (str): SHA-256 of the file.
        bytes (int): File size in bytes.
    """

    path: str = field(validator=validators.instance_of(str))
    sha256: str = field(validator=validators.matches_re(r"^[0-9a-f]{64}$"))
    bytes: int = field(validator=(validators.instance_of(int), validators.ge(0)))


@define
class Rosbag:
    """Source rosbags of the dataset as defined by MOB.

    Attributes:
        log_file_ids (list[str]): Web.Auto log file IDs.
        storage (RosbagStorage | None): rosbag storage format.
        record_start (str): Recording start, ISO 8601 UTC.
        record_end (str): Recording end, ISO 8601 UTC.
    """

    log_file_ids: list[str] = field(
        validator=validators.deep_iterable(
            validators.instance_of(str), validators.instance_of(list)
        )
    )
    storage: RosbagStorage | None = field(converter=converters.optional(RosbagStorage))
    record_start: str = field(validator=validators.instance_of(str))
    record_end: str = field(validator=validators.instance_of(str))


@define
class Provenance:
    """Where this t4dataset came from.

    Attributes:
        rosbag (Rosbag): Source rosbag.
        topics (dict[str, str]): ROS topic used for each channel.
        process_config_id (str | None): Web.Auto processing configuration ID.
        process_config_version_id (int | None): Web.Auto processing configuration version.
    """

    rosbag: Rosbag = field(
        converter=lambda x: Rosbag(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(Rosbag),
    )
    topics: dict[str, str] = field(
        validator=validators.deep_mapping(
            validators.instance_of(str), validators.instance_of(str), validators.instance_of(dict)
        )
    )
    process_config_id: str | None = field(
        validator=validators.optional(validators.instance_of(str))
    )
    process_config_version_id: int | None = field(
        validator=validators.optional(validators.instance_of(int))
    )


@define
class Manifest:
    """`manifest.json` dataclass.

    Attributes:
        schema_version (str): Version of the dataset specification, e.g. "1.0.0".
        dataset_id (str): Dataset ID.
        version (int): Dataset version.
        created_at (str): Creation time, ISO 8601.
        generators (list[Generator]): Tools and libraries that produced the dataset.
        capabilities (Capabilities): What the dataset contains.
        annotation_specifications (dict[str, AnnotationSpecification]): Specification per task.
        tables (dict[str, TableEntry]): Table files, keyed by table name.
        assets (list[AssetEntry]): Sensor, map and input bag files.
        provenance (Provenance): Where the data came from.
        project_id (str | None): Web.Auto project ID.
        source_project_id (str | None): Web.Auto source project ID.
        is_synthetic (bool): Whether the data is synthetic.
        is_discontinuous (bool | None): Whether the recording has gaps.
        migrated_from_schema_version (str | None): Source version if the dataset was migrated.
        migration_notes (list[str] | None): Notes on anything lost or changed during migration.
    """

    schema_version: str = field(validator=validators.instance_of(str))
    dataset_id: str = field(validator=validators.instance_of(str))
    version: int = field(validator=(validators.instance_of(int), validators.ge(0)))
    created_at: str = field(validator=validators.instance_of(str))
    generators: list[Generator] = field(
        converter=lambda x: [Generator(**v) if isinstance(v, dict) else v for v in x],
        validator=validators.deep_iterable(
            validators.instance_of(Generator), validators.instance_of(list)
        ),
    )
    capabilities: Capabilities = field(
        converter=lambda x: Capabilities(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(Capabilities),
    )
    annotation_specifications: dict[str, AnnotationSpecification] = field(
        converter=lambda x: {
            k: AnnotationSpecification(**v) if isinstance(v, dict) else v for k, v in x.items()
        },
        validator=validators.deep_mapping(
            validators.instance_of(str),
            validators.instance_of(AnnotationSpecification),
            validators.instance_of(dict),
        ),
    )
    tables: dict[str, TableEntry] = field(
        converter=lambda x: {
            k: TableEntry(**v) if isinstance(v, dict) else v for k, v in x.items()
        },
        validator=validators.deep_mapping(
            validators.instance_of(str),
            validators.instance_of(TableEntry),
            validators.instance_of(dict),
        ),
    )
    assets: list[AssetEntry] = field(
        converter=lambda x: [AssetEntry(**v) if isinstance(v, dict) else v for v in x],
        validator=validators.deep_iterable(
            validators.instance_of(AssetEntry), validators.instance_of(list)
        ),
    )
    provenance: Provenance = field(
        converter=lambda x: Provenance(**x) if isinstance(x, dict) else x,
        validator=validators.instance_of(Provenance),
    )
    project_id: str | None = field(validator=validators.optional(validators.instance_of(str)))
    source_project_id: str | None = field(
        validator=validators.optional(validators.instance_of(str))
    )
    is_synthetic: bool = field(validator=validators.instance_of(bool))
    is_discontinuous: bool | None = field(
        validator=validators.optional(validators.instance_of(bool))
    )
    migrated_from_schema_version: str | None = field(
        validator=validators.optional(validators.instance_of(str))
    )
    migration_notes: list[str] | None = field(
        validator=validators.optional(
            validators.deep_iterable(validators.instance_of(str), validators.instance_of(list))
        )
    )

    def listed_paths(self) -> list[str]:
        """Return the path of every file listed: tables, then assets.

        Returns:
            Paths relative to the dataset root.
        """
        return [entry.path for entry in self.tables.values()] + [
            entry.path for entry in self.assets
        ]

    @schema_version.validator
    def _check_schema_version(self, attribute, value: str) -> None:
        major = value.split(".")[0]
        if major != str(SUPPORTED_SCHEMA_MAJOR_VERSION):
            raise ValueError(
                f"Unsupported schema_version {value!r}: "
                f"this t4-devkit reads {SUPPORTED_SCHEMA_MAJOR_VERSION}.x."
            )


def load_manifest(data_root: PathLike) -> Manifest | None:
    """Load `manifest.json` from a dataset root.

    Args:
        data_root (PathLike): Dataset root, i.e. the `<DATASET_ID>/<DATASET_VERSION>` directory.

    Returns:
        The manifest of a T4Dataset 1.0 or later, or None for a 0.x dataset (no `manifest.json`).

    Raises:
        ValueError: If the manifest declares a schema version this t4-devkit does not support.
    """
    filepath = osp.join(data_root, MANIFEST_FILENAME)
    if not osp.exists(filepath):
        return None
    return Manifest(**load_json(filepath))
