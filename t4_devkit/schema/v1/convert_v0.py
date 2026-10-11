from __future__ import annotations

import hashlib
import os.path as osp
from collections import defaultdict
from typing import TYPE_CHECKING, Any

import pypcd4
import yaml
from PIL import Image

from t4_devkit.common.io import V0_BIN_FIELDS, load_json

from .name import SchemaName

if TYPE_CHECKING:
    from t4_devkit.typing import PathLike

__all__ = ["V0_FALLBACKS", "convert_v0"]

# Values 1.0 requires that 0.x never stored. The conversion is best effort: these placeholders
# keep a converted dataset loadable, they are not facts about the dataset.
# `vehicle.model == "unknown"` marks placeholder vehicle dimensions.
V0_FALLBACKS: dict[str, Any] = {
    "vehicle": {
        "model": "unknown",
        "length": 1.0,
        "width": 1.0,
        "height": 1.0,
        "wheel_base": 1.0,
        "rear_axle_to_center": None,
        "sensor_rig_id": None,
    },
    "map": {"map_id": "unknown", "version_id": "unknown", "source": "webauto"},
    "map_filename": "map/lanelet2_map.osm",
    "map_projector_filename": "map/map_projector_info.yaml",
    "ego_pose": {"source": "localization", "frame": "map"},
    "lidar": {"frame_id": "base_link", "is_undistorted": True, "compression": "none"},
    "camera": {"is_rectified": True},
}

# 0.x distortion coefficient count -> 1.0 distortion model.
_DISTORTION_MODELS = {0: "none", 5: "plumb_bob", 8: "rational_polynomial"}


def convert_v0(data_root: PathLike) -> dict[SchemaName, list[dict[str, Any]]]:
    """Read a 0.x dataset as 1.0 table dicts, best effort.

    Only the table files are read (plus one header per LiDAR channel and the map files); sensor
    data files are not rewritten, so frames keep one file each and `frame_index` is None.
    Values that 0.x never stored come from `V0_FALLBACKS`.

    Args:
        data_root (PathLike): Dataset root, i.e. the `<DATASET_ID>/<DATASET_VERSION>` directory.

    Returns:
        Raw 1.0 records per table; empty for tables not converted.
    """
    v0 = defaultdict(list)
    for name in ("log", "map", "scene", "sample", "sample_data", "ego_pose", "sensor"):
        v0[name] = _read_v0_table(data_root, name)
    v0["calibrated_sensor"] = _read_v0_table(data_root, "calibrated_sensor")

    maps = [_convert_map(data_root, record) for record in v0["map"]]
    maps = [record for record in maps if record is not None]
    vehicles, logs = _convert_logs(v0["log"], maps)

    tables: dict[SchemaName, list[dict[str, Any]]] = {name: [] for name in SchemaName}
    tables[SchemaName.LOG] = logs
    tables[SchemaName.VEHICLE] = vehicles
    tables[SchemaName.MAP] = maps
    tables[SchemaName.SCENE] = [_convert_scene(record) for record in v0["scene"]]
    tables[SchemaName.SAMPLE] = [_convert_sample(record) for record in v0["sample"]]
    tables[SchemaName.EGO_POSE] = [_convert_ego_pose(record) for record in v0["ego_pose"]]
    tables[SchemaName.SENSOR] = _convert_sensors(data_root, v0)
    tables[SchemaName.SAMPLE_DATA] = [_convert_sample_data(record) for record in v0["sample_data"]]
    return tables


def _read_v0_table(data_root: PathLike, name: str) -> list[dict[str, Any]]:
    filepath = osp.join(data_root, "annotation", f"{name}.json")
    return load_json(filepath) if osp.exists(filepath) else []


def _none_if_empty(value: Any) -> Any:
    """0.x writes "" for missing values; 1.0 uses None."""
    return None if value == "" else value


def _token(*parts: str) -> str:
    """Deterministic token for a record 0.x does not have."""
    return hashlib.md5("/".join(parts).encode()).hexdigest()


def _convert_map(data_root: PathLike, record: dict[str, Any]) -> dict[str, Any] | None:
    filename = record["filename"] or V0_FALLBACKS["map_filename"]
    filepath = osp.join(data_root, filename)
    if not osp.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    return {
        "token": record["token"],
        "name": None,
        "log_tokens": record["log_tokens"],
        "format": "lanelet2_osm",
        "filename": filename,
        "sha256": sha256,
        "projector": _read_projector(data_root),
        **V0_FALLBACKS["map"],
    }


def _read_projector(data_root: PathLike) -> dict[str, Any]:
    """Read Autoware's `map_projector_info.yaml`, if any."""
    filepath = osp.join(data_root, V0_FALLBACKS["map_projector_filename"])
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


def _convert_logs(
    logs: list[dict[str, Any]], maps: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Convert logs; each gets a `vehicle` row from its 0.x vehicle name."""
    log2map = {log_token: record["token"] for record in maps for log_token in record["log_tokens"]}
    vehicles, converted = [], []
    for record in logs:
        vehicle_token = _token(record["token"], "vehicle")
        vehicles.append(
            {
                "token": vehicle_token,
                "name": _none_if_empty(record["vehicle"]),
                **V0_FALLBACKS["vehicle"],
            }
        )
        converted.append(
            {
                "token": record["token"],
                "logfile": _none_if_empty(record["logfile"]),
                "vehicle_token": vehicle_token,
                "data_captured": record["data_captured"],
                "location": _none_if_empty(record["location"]),
                "map_token": log2map.get(record["token"]),
            }
        )
    return vehicles, converted


def _convert_scene(record: dict[str, Any]) -> dict[str, Any]:
    return {**record, "description": _none_if_empty(record["description"])}


def _convert_sample(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "next": _none_if_empty(record["next"]),
        "prev": _none_if_empty(record["prev"]),
    }


def _convert_ego_pose(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "token": record["token"],
        "translation": record["translation"],
        "rotation": record["rotation"],
        "timestamp": record["timestamp"],
        "twist": record.get("twist"),
        "acceleration": record.get("acceleration"),
        "geocoordinate": record.get("geocoordinate"),
        "covariance": None,
        **V0_FALLBACKS["ego_pose"],
    }


def _convert_sample_data(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "token": record["token"],
        "sample_token": _none_if_empty(record["sample_token"]),
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
        "next": _none_if_empty(record["next"]),
        "prev": _none_if_empty(record["prev"]),
    }


def _convert_sensors(
    data_root: PathLike, v0: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Merge 0.x `sensor` (per channel) and `calibrated_sensor` (per calibration) into 1.0 rows.

    One row per calibration, keeping the `calibrated_sensor` token, indexed in file order.
    """
    sensors = {record["token"]: record for record in v0["sensor"]}
    frames = defaultdict(list)
    for record in v0["sample_data"]:
        frames[record["calibrated_sensor_token"]].append(record)

    converted = []
    for index, calibration in enumerate(v0["calibrated_sensor"]):
        sensor = sensors[calibration["sensor_token"]]
        sensor_frames = frames[calibration["token"]]
        modality = sensor["modality"]
        converted.append(
            {
                "token": calibration["token"],
                "channel": sensor["channel"],
                "index": index,
                "modality": modality,
                "translation": calibration["translation"],
                "rotation": calibration["rotation"],
                "camera": _convert_camera(data_root, calibration, sensor_frames)
                if modality == "camera"
                else None,
                "lidar": _convert_lidar(data_root, sensors, sensor_frames)
                if modality == "lidar"
                else None,
                "radar": None,
                "hardware": None,
            }
        )
    return converted


def _convert_camera(
    data_root: PathLike, calibration: dict[str, Any], frames: list[dict[str, Any]]
) -> dict[str, Any]:
    distortion = calibration["camera_distortion"]
    if len(distortion) not in _DISTORTION_MODELS:
        raise ValueError(f"Unknown 0.x distortion with {len(distortion)} coefficients")
    sized = [record for record in frames if record.get("width") and record.get("height")]
    if sized:
        width, height = sized[0]["width"], sized[0]["height"]
    else:
        with Image.open(osp.join(data_root, frames[0]["filename"])) as image:
            width, height = image.size
    return {
        "width": width,
        "height": height,
        "intrinsic": calibration["camera_intrinsic"],
        "distortion": distortion,
        "distortion_model": _DISTORTION_MODELS[len(distortion)],
        "video": None,
        **V0_FALLBACKS["camera"],
    }


def _convert_lidar(
    data_root: PathLike, sensors: dict[str, dict[str, Any]], frames: list[dict[str, Any]]
) -> dict[str, Any]:
    """LiDAR block from the first frame: its format, its `.info` file (if any) and its header."""
    first = frames[0] if frames else {}
    info_filename = first.get("info_filename")
    info = (
        load_json(osp.join(data_root, info_filename))
        if info_filename and osp.exists(osp.join(data_root, info_filename))
        else {}
    )
    if first.get("fileformat") == "pcd":
        data = pypcd4.PointCloud.from_path(osp.join(data_root, first["filename"])).pc_data
        container_format = "pcd"
        fields = [{"name": name, "dtype": str(data.dtype[name])} for name in data.dtype.names]
    else:
        container_format = "bin"
        num_pts_feats = info.get("num_pts_feats", 5)
        fields = [{"name": name, "dtype": "float32"} for name in V0_BIN_FIELDS[:num_pts_feats]]
    fallbacks = V0_FALLBACKS["lidar"]
    return {
        "container": {
            "format": container_format,
            "path": None,
            "frame_count": len(frames),
            "compression": fallbacks["compression"],
        },
        "fields": fields,
        "source_channels": [
            sensors[source["sensor_token"]]["channel"] for source in info.get("sources", [])
        ],
        "frame_id": fallbacks["frame_id"],
        "is_undistorted": fallbacks["is_undistorted"],
    }
