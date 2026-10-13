from __future__ import annotations

import base64
import hashlib
import os.path as osp
import warnings
from collections import defaultdict
from datetime import datetime, timezone
from glob import glob
from typing import TYPE_CHECKING, Any, ClassVar

import pypcd4
import yaml
from PIL import Image
from pycocotools import mask as cocomask

from t4_devkit.common.io import V0_BIN_FIELDS, load_json
from t4_devkit.schema.tables.visibility import VisibilityLevel as V0VisibilityLevel

from .name import SchemaName
from .sensor import DistortionModel

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ["V0Converter"]

Record = dict[str, Any]


class V0Converter:
    """Read a 0.x dataset as 1.0 table dicts, best effort.

    Only the table files are read (plus one header per LiDAR channel and the map files); sensor
    data files are not rewritten, so frames keep one file each and `frame_index` is None.
    Values that 0.x never stored come from `FALLBACKS`.

    Examples:
        >>> tables = V0Converter(data_root).convert()
    """

    # Values 1.0 requires that 0.x never stored. These placeholders keep a converted dataset
    # loadable, they are not facts about the dataset (listed in `docs/schema/v1/index.md`).
    # `vehicle.model == "unknown"` marks placeholder vehicle dimensions.
    FALLBACKS: ClassVar[dict[str, Any]] = {
        "vehicle": {
            "model": "unknown",
            "length": 1.0,
            "width": 1.0,
            "height": 1.0,
            "wheel_base": 1.0,
        },
        "map": {"map_id": "unknown", "version_id": "unknown", "source": "webauto"},
        "map_filename": "map/lanelet2_map.osm",
        "map_projector_filename": "map/map_projector_info.yaml",
        "ego_pose": {"source": "localization", "frame": "map"},
        "lidar": {"frame_id": "base_link", "is_undistorted": True, "compression": "none"},
        "camera": {"is_rectified": True},
    }

    def __init__(self, data_root: PathLike) -> None:
        """
        Args:
            data_root (PathLike): Dataset root, i.e. the `<DATASET_ID>/<DATASET_VERSION>` directory.
        """
        self.data_root = data_root
        # Every 0.x table file present, by table name; a missing table reads as empty.
        self.v0: dict[str, list[Record]] = defaultdict(list)
        for filepath in glob(osp.join(data_root, "annotation", "*.json")):
            self.v0[osp.splitext(osp.basename(filepath))[0]] = load_json(filepath)

        # Lookups shared by several tables.
        self.sensors = {record["token"]: record for record in self.v0["sensor"]}
        self.frames: dict[str, list[Record]] = defaultdict(list)
        for record in self.v0["sample_data"]:
            self.frames[record["calibrated_sensor_token"]].append(record)
        self.thing_categories = {
            record["category_token"] for record in self.v0["object_ann"] + self.v0["instance"]
        }
        self.surface_categories = {record["category_token"] for record in self.v0["surface_ann"]}
        self.infos: dict[str, list[Record]] = {}  # filled by `_frame_infos`
        self.traffic_light_ways = self._traffic_light_ways()

    def convert(self) -> dict[SchemaName, list[Record]]:
        """Convert every table.

        Returns:
            Raw 1.0 records per table; empty for tables not converted.
        """
        v0 = self.v0
        maps = [self.convert_map(record) for record in v0["map"]]
        maps = [record for record in maps if record is not None]
        log2map = {token: record["token"] for record in maps for token in record["log_tokens"]}
        visibilities = self.convert_visibilities()
        known_visibility = {record["token"] for record in visibilities}

        tables: dict[SchemaName, list[Record]] = {name: [] for name in SchemaName}
        tables[SchemaName.MAP] = maps
        tables[SchemaName.VEHICLE] = [self.convert_vehicle(record) for record in v0["log"]]
        tables[SchemaName.LOG] = [self.convert_log(record, log2map) for record in v0["log"]]
        tables[SchemaName.SCENE] = [self.convert_scene(record) for record in v0["scene"]]
        tables[SchemaName.SAMPLE] = [self.convert_sample(record) for record in v0["sample"]]
        tables[SchemaName.EGO_POSE] = [self.convert_ego_pose(record) for record in v0["ego_pose"]]
        tables[SchemaName.SENSOR] = [
            self.convert_sensor(index, record)
            for index, record in enumerate(v0["calibrated_sensor"])
        ]
        tables[SchemaName.SAMPLE_DATA] = [
            self.convert_sample_data(record) for record in v0["sample_data"]
        ]

        tables[SchemaName.CATEGORY] = [self.convert_category(record) for record in v0["category"]]
        tables[SchemaName.ATTRIBUTE] = [
            self.convert_attribute(record) for record in v0["attribute"]
        ]
        tables[SchemaName.VISIBILITY] = visibilities
        tables[SchemaName.INSTANCE] = [self.convert_instance(record) for record in v0["instance"]]
        tables[SchemaName.SAMPLE_ANNOTATION] = [
            self.convert_sample_annotation(record, known_visibility)
            for record in v0["sample_annotation"]
        ]
        tables[SchemaName.OBJECT_ANN] = [
            self.convert_object_ann(record) for record in v0["object_ann"]
        ] + [self.convert_surface_ann(record) for record in v0["surface_ann"]]
        tables[SchemaName.KEYPOINT] = [self.convert_keypoint(record) for record in v0["keypoint"]]
        tables[SchemaName.VEHICLE_STATE] = [
            self.convert_vehicle_state(record) for record in v0["vehicle_state"]
        ]
        return tables

    # --- core tables ---

    def convert_map(self, record: Record) -> Record | None:
        """`sha256` from the map file, `projector` from its yaml; None if the map file is missing."""
        filename = record["filename"] or self.FALLBACKS["map_filename"]
        filepath = osp.join(self.data_root, filename)
        if not osp.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        fallbacks = self.FALLBACKS["map"]
        return {
            "token": record["token"],
            "name": None,
            "log_tokens": record["log_tokens"],
            "map_id": fallbacks["map_id"],
            "version_id": fallbacks["version_id"],
            "source": fallbacks["source"],
            "format": "lanelet2_osm",
            "filename": filename,
            "sha256": sha256,
            "projector": self._read_projector(),
        }

    def convert_vehicle(self, log: Record) -> Record:
        """One vehicle per log, named after the 0.x `log.vehicle`, with placeholder dimensions."""
        fallbacks = self.FALLBACKS["vehicle"]
        return {
            "token": self._vehicle_token(log),
            "name": self._none_if_empty(log["vehicle"]),
            "model": fallbacks["model"],
            "length": fallbacks["length"],
            "width": fallbacks["width"],
            "height": fallbacks["height"],
            "wheel_base": fallbacks["wheel_base"],
            "rear_axle_to_center": None,
            "sensor_rig_id": None,
        }

    def convert_log(self, record: Record, log2map: dict[str, str]) -> Record:
        return {
            "token": record["token"],
            "logfile": self._none_if_empty(record["logfile"]),
            "vehicle_token": self._vehicle_token(record),
            "data_captured": record["data_captured"] or self._capture_time(record["token"]),
            "location": self._none_if_empty(record["location"]),
            "map_token": log2map.get(record["token"]),
        }

    def convert_scene(self, record: Record) -> Record:
        return {
            "token": record["token"],
            "name": record["name"],
            "description": self._none_if_empty(record["description"]),
            "log_token": record["log_token"],
            "nbr_samples": record["nbr_samples"],
            "first_sample_token": record["first_sample_token"],
            "last_sample_token": record["last_sample_token"],
        }

    def convert_sample(self, record: Record) -> Record:
        return {
            "token": record["token"],
            "timestamp": record["timestamp"],
            "scene_token": record["scene_token"],
            "next": self._none_if_empty(record["next"]),
            "prev": self._none_if_empty(record["prev"]),
        }

    def convert_ego_pose(self, record: Record) -> Record:
        fallbacks = self.FALLBACKS["ego_pose"]
        return {
            "token": record["token"],
            "translation": record["translation"],
            "rotation": record["rotation"],
            "timestamp": record["timestamp"],
            "twist": record.get("twist"),
            "acceleration": record.get("acceleration"),
            "geocoordinate": record.get("geocoordinate"),
            "covariance": None,
            "source": fallbacks["source"],
            "frame": fallbacks["frame"],
        }

    def convert_sensor(self, index: int, calibration: Record) -> Record:
        """Merge 0.x `sensor` (per channel) and `calibrated_sensor` (per calibration).

        One row per calibration, keeping the `calibrated_sensor` token, indexed in file order.
        """
        sensor = self.sensors[calibration["sensor_token"]]
        modality = sensor["modality"]
        return {
            "token": calibration["token"],
            "channel": sensor["channel"],
            "index": index,
            "modality": modality,
            "translation": calibration["translation"],
            "rotation": calibration["rotation"],
            "camera": self.convert_camera(calibration) if modality == "camera" else None,
            "lidar": self.convert_lidar(calibration) if modality == "lidar" else None,
            "radar": None,
            "hardware": None,
        }

    def convert_camera(self, calibration: Record) -> Record:
        """Size from `sample_data`, or from the first image if 0.x stored none."""
        distortion = calibration["camera_distortion"]
        distortion_model = DistortionModel.from_num_coefficients(len(distortion))
        frames = self.frames[calibration["token"]]
        sized = [record for record in frames if record.get("width") and record.get("height")]
        if sized:
            width, height = sized[0]["width"], sized[0]["height"]
        else:
            with Image.open(osp.join(self.data_root, frames[0]["filename"])) as image:
                width, height = image.size
        return {
            "width": width,
            "height": height,
            "intrinsic": calibration["camera_intrinsic"],
            "distortion": distortion,
            "distortion_model": distortion_model.value,
            "is_rectified": self.FALLBACKS["camera"]["is_rectified"],
            "video": None,
        }

    def convert_lidar(self, calibration: Record) -> Record:
        """From the first frame: its format, its `.info` file (if any) and its header."""
        frames = self.frames[calibration["token"]]
        if not frames:
            return self._convert_source_lidar(calibration)
        first = frames[0]
        info = self._frame_infos(calibration["token"])[0]
        if first["fileformat"] == "pcd":
            filepath = osp.join(self.data_root, first["filename"])
            data = pypcd4.PointCloud.from_path(filepath).pc_data
            container_format = "pcd"
            fields = [{"name": name, "dtype": str(data.dtype[name])} for name in data.dtype.names]
        else:
            container_format = "bin"
            num_pts_feats = info.get("num_pts_feats", 5)
            fields = [{"name": name, "dtype": "float32"} for name in V0_BIN_FIELDS[:num_pts_feats]]
        fallbacks = self.FALLBACKS["lidar"]
        return {
            "container": {
                "format": container_format,
                "path": None,
                "frame_count": len(frames),
                "compression": fallbacks["compression"],
            },
            "fields": fields,
            "source_channels": [
                self.sensors[source["sensor_token"]]["channel"]
                for source in info.get("sources", [])
            ],
            "frame_id": fallbacks["frame_id"],
            "is_undistorted": fallbacks["is_undistorted"],
        }

    def convert_sample_data(self, record: Record) -> Record:
        return {
            "token": record["token"],
            "sample_token": self._none_if_empty(record["sample_token"]),
            "ego_pose_token": record["ego_pose_token"],
            # 0.x calibrated_sensor rows become 1.0 sensor rows, with the same tokens.
            "sensor_token": record["calibrated_sensor_token"],
            "filename": record["filename"],
            "frame_index": None,
            "fileformat": record["fileformat"],
            "num_points": None,
            "timestamp": record["timestamp"],
            "is_key_frame": record["is_key_frame"],
            "is_valid": record.get("is_valid", True),
            "next": self._none_if_empty(record["next"]),
            "prev": self._none_if_empty(record["prev"]),
        }

    # --- label tables ---

    def convert_category(self, record: Record) -> Record:
        """`is_thing` is false only for categories used by `surface_ann` (road, sky) and nothing else."""
        token = record["token"]
        return {
            "token": token,
            "name": record["name"],
            "index": record.get("index"),
            "description": self._none_if_empty(record.get("description")),
            "is_thing": token in self.thing_categories or token not in self.surface_categories,
            "has_orientation": record.get("has_orientation", False),
            "has_number": record.get("has_number", False),
        }

    def convert_attribute(self, record: Record) -> Record:
        return {
            "token": record["token"],
            "name": record["name"],
            "description": self._none_if_empty(record.get("description")),
        }

    def convert_visibilities(self) -> list[Record]:
        """Levels as read by 0.x (aliases mapped); `unavailable` rows are dropped (visibility unknown)."""
        rows = []
        for record in self.v0["visibility"]:
            level = V0VisibilityLevel.from_value(record["level"])
            if level != V0VisibilityLevel.UNAVAILABLE:
                rows.append(
                    {
                        "token": record["token"],
                        "level": level.value,
                        "description": self._none_if_empty(record.get("description")),
                    }
                )
        return rows

    def convert_instance(self, record: Record) -> Record:
        """A lamp listed in 0.x traffic_light points to its lanelet2 way in `map_element`."""
        way_id = self.traffic_light_ways.get(record["token"])
        return {
            "token": record["token"],
            "name": record["instance_name"],
            "index": None,
            "category_token": record["category_token"],
            "nbr_annotations": record["nbr_annotations"],
            "first_annotation_token": self._none_if_empty(record["first_annotation_token"]),
            "last_annotation_token": self._none_if_empty(record["last_annotation_token"]),
            "map_element": {"id": way_id, "type": "way" if way_id is not None else None},
        }

    def convert_sample_annotation(self, record: Record, known_visibility: set[str]) -> Record:
        """Visibility levels dropped by `convert_visibilities` become a null `visibility_token`."""
        visibility_token = record["visibility_token"]
        annotation_type, provenance, confidence = self._label_origin(record)
        return {
            "token": record["token"],
            "sample_token": record["sample_token"],
            "instance_token": record["instance_token"],
            "attribute_tokens": record["attribute_tokens"],
            "visibility_token": visibility_token if visibility_token in known_visibility else None,
            "translation": record["translation"],
            "size": record["size"],
            "rotation": record["rotation"],
            "velocity": record.get("velocity"),
            "acceleration": record.get("acceleration"),
            "num_lidar_pts": record["num_lidar_pts"],
            "num_radar_pts": record["num_radar_pts"],
            "next": self._none_if_empty(record["next"]),
            "prev": self._none_if_empty(record["prev"]),
            "annotation_type": annotation_type,
            "provenance": provenance,
            "confidence": confidence,
        }

    def convert_object_ann(self, record: Record) -> Record:
        annotation_type, provenance, confidence = self._label_origin(record)
        return {
            "token": record["token"],
            "sample_data_token": record["sample_data_token"],
            "instance_token": record["instance_token"],
            "category_token": record["category_token"],
            "attribute_tokens": record["attribute_tokens"],
            # 0.x leaves bbox out for mask-only labels; 1.0 requires it.
            "bbox": record.get("bbox") or self._mask_bbox(record["mask"]),
            "mask": self._non_empty_mask(record.get("mask")),
            "orientation": record.get("orientation"),
            "number": record.get("number"),
            "annotation_type": annotation_type,
            "provenance": provenance,
            "confidence": confidence,
        }

    def convert_surface_ann(self, record: Record) -> Record:
        """A 0.x semantic mask becomes an `object_ann` without instance; its box is the mask's."""
        mask = record["mask"]
        annotation_type, provenance, confidence = self._label_origin(record)
        return {
            "token": record["token"],
            "sample_data_token": record["sample_data_token"],
            "instance_token": None,
            "category_token": record["category_token"],
            "attribute_tokens": [],
            "bbox": self._mask_bbox(mask),
            "mask": mask,
            "orientation": None,
            "number": None,
            "annotation_type": annotation_type,
            "provenance": provenance,
            "confidence": confidence,
        }

    def convert_keypoint(self, record: Record) -> Record:
        annotation_type, provenance, confidence = self._label_origin(record)
        return {
            "token": record["token"],
            "sample_data_token": record["sample_data_token"],
            "instance_token": record["instance_token"],
            "category_tokens": record["category_tokens"],
            "keypoints": record["keypoints"],
            "num_keypoints": record["num_keypoints"],
            "annotation_type": annotation_type,
            "provenance": provenance,
            "confidence": confidence,
        }

    # --- planning tables ---

    def convert_vehicle_state(self, record: Record) -> Record:
        """0.x vehicle states come from the Autoware vehicle interface (`/vehicle/status/*`).

        `additional_info.speed` (norm of the longitudinal and lateral velocity) is dropped: it can't
        be split back into the 1.0 velocities.
        """
        shift_state = record.get("shift_state")
        # The 0.x devkit names forward gears FORWARD or HIGH; the 0.x converter writes DRIVE.
        if shift_state in ("FORWARD", "HIGH"):
            shift_state = "DRIVE"
        return {
            "token": record["token"],
            "timestamp": record["timestamp"],
            "accel_pedal": record.get("accel_pedal"),
            "brake_pedal": record.get("brake_pedal"),
            "steer_pedal": record.get("steer_pedal"),
            "steering_tire_angle": record.get("steering_tire_angle"),
            "steering_wheel_angle": record.get("steering_wheel_angle"),
            "shift_state": shift_state,
            "indicators": record.get("indicators"),
            "longitudinal_velocity": None,
            "lateral_velocity": None,
            "heading_rate": None,
            "source": "vehicle_interface",
        }

    # --- helpers ---

    def _read_projector(self) -> Record:
        """Read Autoware's `map_projector_info.yaml`, if any."""
        filepath = osp.join(self.data_root, self.FALLBACKS["map_projector_filename"])
        info = {}
        if osp.exists(filepath):
            with open(filepath) as f:
                info = yaml.safe_load(f) or {}
        origin = info.get("map_origin") or {}
        return {
            "type": info.get("projector_type"),
            "mgrs_grid": info.get("mgrs_grid"),
            "origin": {
                "lat": origin.get("latitude"),
                "lon": origin.get("longitude"),
                "alt": origin.get("altitude"),
            },
        }

    def _convert_source_lidar(self, calibration: Record) -> Record:
        """A LiDAR without frames of its own: a source of a concatenated channel.

        Its points are stored in the concatenated files, so it has their format and fields; it
        counts a frame wherever the `.info` file of a concatenated frame lists points from it.
        """
        sensor_token = calibration["sensor_token"]
        fallbacks = self.FALLBACKS["lidar"]
        container_format, fields, frame_count = "bin", [], 0
        for concat in self.v0["calibrated_sensor"]:
            infos = self._frame_infos(concat["token"])
            lengths = [
                sum(
                    s["length"]
                    for s in info.get("sources", [])
                    if s["sensor_token"] == sensor_token
                )
                for info in infos
            ]
            if any(lengths):
                concat_lidar = self.convert_lidar(concat)
                container_format = concat_lidar["container"]["format"]
                fields = concat_lidar["fields"]
                frame_count = sum(length > 0 for length in lengths)
                break
        return {
            "container": {
                "format": container_format,
                "path": None,
                "frame_count": frame_count,
                "compression": fallbacks["compression"],
            },
            "fields": fields,
            "source_channels": [],
            "frame_id": fallbacks["frame_id"],
            "is_undistorted": fallbacks["is_undistorted"],
        }

    def _capture_time(self, log_token: str) -> str:
        """The log's first sample time, ISO 8601 UTC, for logs without `data_captured`."""
        scenes = {
            record["token"] for record in self.v0["scene"] if record["log_token"] == log_token
        }
        timestamp = min(
            record["timestamp"] for record in self.v0["sample"] if record["scene_token"] in scenes
        )
        return datetime.fromtimestamp(timestamp / 1e6, tz=timezone.utc).isoformat()

    def _traffic_light_ways(self) -> dict[str, int]:
        """The lanelet2 way (`type=traffic_light`) each lamp instance shows, by instance token.

        Two 0.x tables hold this link: `traffic_light` (`primitive_id`, #288) and
        `traffic_light_instance_map` (`traffic_light_linestring_id`, from the unmerged
        `feat/traffic-light-instance-map` branch), which wins when both list a lamp.
        `traffic_light` rows without `primitive_id` are skipped, as no 0.x devkit reads them.
        """
        ways = {}
        skipped = 0
        for record in self.v0["traffic_light"]:
            if "primitive_id" in record:
                ways[record["instance_token"]] = int(record["primitive_id"])
            else:
                skipped += 1
        if skipped:
            warnings.warn(f"Skipped {skipped} traffic_light rows without primitive_id")
        for record in self.v0["traffic_light_instance_map"]:
            ways[record["instance_token"]] = int(record["traffic_light_linestring_id"])
        return ways

    def _frame_infos(self, calibration_token: str) -> list[Record]:
        """The 0.x `.info` file of each frame of a channel ({} where there is none), read once."""
        if calibration_token not in self.infos:
            self.infos[calibration_token] = [
                load_json(osp.join(self.data_root, frame["info_filename"]))
                if frame.get("info_filename")
                and osp.exists(osp.join(self.data_root, frame["info_filename"]))
                else {}
                for frame in self.frames[calibration_token]
            ]
        return self.infos[calibration_token]

    @staticmethod
    def _non_empty_mask(mask: Record | None) -> Record | None:
        """None for a mask without pixels.

        Some 0.x tools give box-only labels a placeholder: an empty RLE whose `size` is
        (width, height) instead of the (height, width) of real masks.
        """
        if mask is None or "counts" not in mask:
            return None
        rle = {"counts": base64.b64decode(mask["counts"]), "size": mask["size"]}
        return mask if cocomask.area(rle) > 0 else None

    @staticmethod
    def _mask_bbox(mask: Record) -> list[float]:
        """Box around a 0.x RLE mask, as (xmin, ymin, xmax, ymax) on pixel edges.

        Same convention as 0.x boxes, which the 0.x converter writes as (x, y, x + w, y + h)
        clipped to the image size. Mask `size` is (height, width), as in COCO.
        """
        rle = {"counts": base64.b64decode(mask["counts"]), "size": mask["size"]}
        x, y, w, h = (float(v) for v in cocomask.toBbox(rle))
        return [x, y, x + w, y + h]

    @staticmethod
    def _vehicle_token(log: Record) -> str:
        """Deterministic token: 0.x has no vehicle table."""
        return hashlib.md5(f"{log['token']}/vehicle".encode()).hexdigest()

    @staticmethod
    def _none_if_empty(value: Any) -> Any:
        """0.x writes "" for missing values; 1.0 uses None."""
        return None if value == "" else value

    @staticmethod
    def _label_origin(record: Record) -> tuple[str, str | None, float | None]:
        """`annotation_type`, `provenance` and `confidence` from the 0.x autolabel fields.

        Manual unless 0.x marks the label as automatic. `provenance` lists the autolabel models;
        `confidence` is the model score when there is exactly one model.
        """
        if not record.get("automatic_annotation", False):
            return "manual", None, None
        models = record.get("autolabel_metadata") or []
        provenance = ", ".join(model["name"] for model in models) or None
        confidence = models[0]["score"] if len(models) == 1 else None
        return "auto", provenance, confidence
