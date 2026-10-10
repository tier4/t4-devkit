from __future__ import annotations

from enum import Enum, unique

__all__ = ["SchemaName"]


@unique
class SchemaName(str, Enum):
    """Names of the T4Dataset 1.0 tables, one JSON file each in `annotation/`.

    Required tables: sample, sample_data, ego_pose, sensor, scene, log, vehicle.
    All other tables are optional; `manifest.json` declares which ones a dataset contains.
    """

    SAMPLE = "sample"
    SAMPLE_DATA = "sample_data"
    EGO_POSE = "ego_pose"
    SENSOR = "sensor"
    SCENE = "scene"
    LOG = "log"
    VEHICLE = "vehicle"
    MAP = "map"  # optional
    VEHICLE_STATE = "vehicle_state"  # optional
    CATEGORY = "category"  # optional
    ATTRIBUTE = "attribute"  # optional
    VISIBILITY = "visibility"  # optional
    INSTANCE = "instance"  # optional
    SAMPLE_ANNOTATION = "sample_annotation"  # optional
    OBJECT_ANN = "object_ann"  # optional
    KEYPOINT = "keypoint"  # optional
    TRAFFIC_LIGHT = "traffic_light"  # optional
    ROUTE = "route"  # optional
    SCENARIO = "scenario"  # optional
    CAPTION = "caption"  # optional

    @property
    def filename(self) -> str:
        """Return the annotation json filename.

        Returns:
            Annotation json filename.
        """
        return f"{self.value}.json"

    def is_optional(self) -> bool:
        """Indicates if this table is optional.

        Returns:
            Return True if this table is optional.
        """
        return self not in (
            SchemaName.SAMPLE,
            SchemaName.SAMPLE_DATA,
            SchemaName.EGO_POSE,
            SchemaName.SENSOR,
            SchemaName.SCENE,
            SchemaName.LOG,
            SchemaName.VEHICLE,
        )
