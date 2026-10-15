"""Generate the T4Dataset 1.0 sample in this directory.

Three samples (frames): two key frames with one camera (CAM_FRONT, AV1) and one LiDAR
(LIDAR_TOP, Parquet) frame each, then a non-key frame with a LiDAR frame only (a channel can be
missing). One record in every optional table. All data is synthetic and deterministic.

Written with `DatasetWriter`, like a real dataset (no FFmpeg needed):

    python tests/sample/t4dataset_v1/make_sample_v1.py
"""

from __future__ import annotations

import base64
import hashlib
import shutil
import tempfile
from pathlib import Path

import numpy as np
from pycocotools import mask as cocomask

from t4_devkit.schema.v1 import SCHEMAS, DatasetWriter, SchemaName

ROOT = Path(__file__).parent

NUM_FRAMES = 2  # key frames, with a camera and a LiDAR frame each
NUM_SAMPLES = NUM_FRAMES + 1  # the last sample is a non-key frame with a LiDAR frame only
FPS = 10
WIDTH, HEIGHT = 64, 48
NUM_POINTS = 8
T0 = 1704067200000000  # 2024-01-01T00:00:00Z in microseconds
DT = 1_000_000 // FPS

LIDAR_FIELDS = [
    ("x", "float32"),
    ("y", "float32"),
    ("z", "float32"),
    ("intensity", "float32"),
    ("ring", "uint16"),
]
MAP_PATH = "map/lanelet2_map.osm"


def road_mask() -> dict[str, object]:
    """RLE mask of the road: the bottom half of the image (rows 24-47), as pycocotools writes it."""
    mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8, order="F")
    mask[24:, :] = 1
    rle = cocomask.encode(mask)
    return {"size": [HEIGHT, WIDTH], "counts": base64.b64encode(rle["counts"]).decode()}


def camera_frames() -> list[np.ndarray]:
    """NUM_FRAMES synthetic RGB frames."""
    frames = []
    for i in range(NUM_FRAMES):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        frame[:, :, 0] = np.linspace(0, 255, WIDTH, dtype=np.uint8)
        frame[:, :, 1] = 128 * i
        frames.append(frame)
    return frames


def lidar_frames() -> list[dict[str, np.ndarray]]:
    """NUM_SAMPLES frames of NUM_POINTS points."""
    rng = np.random.default_rng(0)
    frames = []
    for _ in range(NUM_SAMPLES):
        xyzi = rng.uniform(-10, 10, (NUM_POINTS, 4)).astype(np.float32)
        frame = {name: xyzi[:, k] for k, (name, _) in enumerate(LIDAR_FIELDS[:4])}
        frame["ring"] = np.arange(NUM_POINTS, dtype=np.uint16)
        frames.append(frame)
    return frames


# Added to the 0.x sample's map: a traffic light (way) and its regulatory element, controlling
# the main road lanelet 1000.
TRAFFIC_LIGHT_WAY = 200
TRAFFIC_LIGHT_REGULATORY_ELEMENT = 2000
LANELETS = [1000, 1001]
MAP_ADDITIONS = f"""
  <!-- Traffic light and its regulatory element (added for the 1.0 sample) -->
  <way id="{TRAFFIC_LIGHT_WAY}">
    <nd ref="1"/>
    <nd ref="2"/>
    <tag k="type" v="traffic_light"/>
    <tag k="subtype" v="red_yellow_green"/>
  </way>
  <relation id="{TRAFFIC_LIGHT_REGULATORY_ELEMENT}">
    <member type="way" ref="{TRAFFIC_LIGHT_WAY}" role="refers"/>
    <tag k="type" v="regulatory_element"/>
    <tag k="subtype" v="traffic_light"/>
  </relation>

</osm>
"""


def write_map(path: Path) -> None:
    """Write the 0.x sample's map with the traffic light added."""
    osm = (ROOT.parent / "t4dataset" / MAP_PATH).read_text()
    path.write_text(osm.replace("\n</osm>\n", MAP_ADDITIONS))


def label(
    annotation_type: str = "manual",
    provenance: str | None = None,
    confidence: float | None = None,
) -> dict:
    return {"annotation_type": annotation_type, "provenance": provenance, "confidence": confidence}


def tables(camera_video: dict, lidar_path: str, map_sha256: str) -> dict[str, list[dict]]:
    identity = [1.0, 0.0, 0.0, 0.0]
    zero = [0.0, 0.0, 0.0]
    samples = [f"sample{i}" for i in range(NUM_SAMPLES)]
    timestamps = [T0 + i * DT for i in range(NUM_SAMPLES)]

    def link(tokens: list[str], i: int) -> dict:
        return {
            "next": tokens[i + 1] if i + 1 < len(tokens) else None,
            "prev": tokens[i - 1] if i > 0 else None,
        }

    sample_data = []
    ego_pose = []
    for channel, sensor, path, fileformat, num_points, num_frames in (
        ("cam", "sensor_cam", camera_video["path"], "av1_mp4", None, NUM_FRAMES),
        ("lidar", "sensor_lidar", lidar_path, "parquet", NUM_POINTS, NUM_SAMPLES),
    ):
        tokens = [f"{channel}{i}" for i in range(num_frames)]
        for i, token in enumerate(tokens):
            sample_data.append(
                {
                    "token": token,
                    "sample_token": samples[i],
                    "ego_pose_token": f"ego_{token}",
                    "sensor_token": sensor,
                    "filename": path,
                    "frame_index": i,
                    "fileformat": fileformat,
                    "num_points": num_points,
                    "timestamp": timestamps[i],
                    "is_key_frame": i < NUM_FRAMES,
                    "is_valid": True,
                }
                | link(tokens, i)
            )
            ego_pose.append(
                {
                    "token": f"ego_{token}",
                    "translation": [float(i), 0.0, 0.0],
                    "rotation": identity,
                    "timestamp": timestamps[i],
                    "twist": None,
                    "acceleration": None,
                    "geocoordinate": None,
                    "source": "localization",
                    "frame": "map",
                    "covariance": None,
                }
            )

    sample_annotations = [f"box{i}" for i in range(NUM_FRAMES)]
    return {
        "sample": [
            {
                "token": s,
                "timestamp": timestamps[i],
                "scene_token": "scene",
                "has_key_frame": i < NUM_FRAMES,
            }
            | link(samples, i)
            for i, s in enumerate(samples)
        ],
        "sample_data": sample_data,
        "ego_pose": ego_pose,
        "sensor": [
            {
                "token": "sensor_cam",
                "channel": "CAM_FRONT",
                "index": 0,
                "modality": "camera",
                "translation": [1.0, 0.0, 1.5],
                "rotation": [0.5, -0.5, 0.5, -0.5],
                "camera": {
                    "width": WIDTH,
                    "height": HEIGHT,
                    "intrinsic": [[50.0, 0.0, 32.0], [0.0, 50.0, 24.0], [0.0, 0.0, 1.0]],
                    "distortion": [0.0, 0.0, 0.0, 0.0, 0.0],
                    "distortion_model": "plumb_bob",
                    "is_rectified": False,
                    "video": camera_video,
                },
                "lidar": None,
                "radar": None,
                "hardware": {
                    "make": "Sony",
                    "model": "IMX728",
                    "serial_number": None,
                    "firmware_version": None,
                },
            },
            {
                "token": "sensor_lidar",
                "channel": "LIDAR_TOP",
                "index": 1,
                "modality": "lidar",
                "translation": [0.0, 0.0, 2.0],
                "rotation": identity,
                "camera": None,
                "lidar": {
                    "container": {
                        "format": "parquet",
                        "path": lidar_path,
                        "frame_count": NUM_SAMPLES,
                        "compression": "zstd",
                    },
                    "fields": [{"name": name, "dtype": dtype} for name, dtype in LIDAR_FIELDS],
                    "source_channels": [],
                    "frame_id": "base_link",
                    "is_undistorted": True,
                },
                "radar": None,
                "hardware": {
                    "make": "Hesai",
                    "model": "OT128",
                    "serial_number": None,
                    "firmware_version": None,
                },
            },
        ],
        "scene": [
            {
                "token": "scene",
                "name": "sample_scene",
                "description": None,
                "log_token": "log",
                "nbr_samples": NUM_SAMPLES,
                "first_sample_token": samples[0],
                "last_sample_token": samples[-1],
            }
        ],
        "log": [
            {
                "token": "log",
                "logfile": None,
                "vehicle_token": "vehicle",
                "data_captured": "2024-01-01T00:00:00Z",
                "location": None,
                "map_token": "map",
            }
        ],
        "vehicle": [
            {
                "token": "vehicle",
                "name": None,
                "model": "sample_vehicle",
                "length": 4.9,
                "width": 1.9,
                "height": 2.0,
                "wheel_base": 2.8,
                "rear_axle_to_center": None,
                "sensor_rig_id": None,
            }
        ],
        "map": [
            {
                "token": "map",
                "name": None,
                "log_tokens": ["log"],
                "format": "lanelet2_osm",
                "filename": MAP_PATH,
                "sha256": map_sha256,
                "map_id": "sample_map",
                "version_id": "sample_map_version",
                "projector": {
                    "type": "MGRS",
                    "mgrs_grid": "54SUE",
                    "origin": {"lat": None, "lon": None, "alt": None},
                },
                "source": "manual",
            }
        ],
        "vehicle_state": [
            {
                "token": "vehicle_state0",
                "timestamp": timestamps[0],
                "accel_pedal": 0.0,
                "brake_pedal": 0.0,
                "steer_pedal": None,
                "steering_tire_angle": 0.0,
                "steering_wheel_angle": None,
                "shift_state": "DRIVE",
                "indicators": {"left": "off", "right": "off", "hazard": "off"},
                "longitudinal_velocity": 1.0,
                "lateral_velocity": 0.0,
                "heading_rate": 0.0,
                "source": "vehicle_interface",
            }
        ],
        "category": [
            {
                "token": "category_car",
                "name": "car",
                "index": None,
                "description": None,
                "is_thing": True,
                "has_orientation": False,
                "has_number": False,
            },
            {
                "token": "category_road",
                "name": "road",
                "index": None,
                "description": None,
                "is_thing": False,
                "has_orientation": False,
                "has_number": False,
            },
        ],
        "attribute": [
            {"token": "attribute_moving", "name": "vehicle_state.moving", "description": None}
        ],
        "visibility": [{"token": "visibility_full", "level": "full", "description": None}],
        "instance": [
            {
                "token": "instance_car",
                "name": "sample::0",
                "index": None,
                "category_token": "category_car",
                # its 3D boxes and its 2D label
                "nbr_annotations": NUM_FRAMES + 1,
                "first_annotation_token": sample_annotations[0],
                "last_annotation_token": sample_annotations[-1],
                "map_element": {"id": None, "type": None},
            }
        ],
        "sample_annotation": [
            {
                "token": token,
                "sample_token": samples[i],
                "instance_token": "instance_car",
                "attribute_tokens": ["attribute_moving"],
                "visibility_token": "visibility_full",
                "translation": [10.0 + i, 0.0, 1.0],
                "size": [1.9, 4.5, 1.6],
                "rotation": identity,
                "velocity": [1.0, 0.0, 0.0],
                "acceleration": None,
                "num_lidar_pts": 0,
                "num_radar_pts": None,
            }
            | link(sample_annotations, i)
            | (label() if i == 0 else label("interpolated", provenance="t4-devkit interpolation"))
            for i, token in enumerate(sample_annotations)
        ],
        "object_ann": [
            {
                "token": "object_ann0",
                "sample_data_token": "cam0",
                "instance_token": "instance_car",
                "category_token": "category_car",
                "attribute_tokens": [],
                "bbox": [10.0, 10.0, 30.0, 20.0],
                "mask": None,
                "orientation": None,
                "number": None,
            }
            | label(),
            {
                "token": "object_ann1",
                "sample_data_token": "cam0",
                "instance_token": None,
                "category_token": "category_road",
                "attribute_tokens": [],
                "bbox": [0.0, 24.0, float(WIDTH), float(HEIGHT)],
                "mask": road_mask(),
                "orientation": None,
                "number": None,
            }
            | label(),
        ],
        "keypoint": [
            {
                "token": "keypoint0",
                "sample_data_token": "cam0",
                "instance_token": "instance_car",
                "category_tokens": ["category_car"],
                "keypoints": [[12.0, 18.0]],
                "num_keypoints": 1,
            }
            | label()
        ],
        "traffic_light": [
            {
                "token": "traffic_light0",
                "timestamp": timestamps[0],
                "regulatory_element_id": TRAFFIC_LIGHT_REGULATORY_ELEMENT,
                "elements": [
                    {"color": "green", "shape": "circle", "status": "solid_on", "confidence": 1.0}
                ],
                "object_ann_token": None,
                "instance_token": None,
            }
            | label("auto", provenance="sample recognizer", confidence=0.9)
        ],
        "route": [
            {
                "token": "route0",
                "log_token": "log",
                "map_token": "map",
                "valid_from": timestamps[0],
                "valid_until": None,
                "route_uuid": None,
                "start_pose": {"translation": zero, "rotation": identity},
                "goal_pose": {"translation": [100.0, 0.0, 0.0], "rotation": identity},
                "segments": [{"preferred_primitive_id": LANELETS[0], "primitive_ids": LANELETS}],
                "allow_modification": False,
                "source": "mission_planner",
                "provenance": "own_bag",
            }
        ],
        "scenario": [
            {
                "token": "scenario0",
                "log_token": "log",
                "start_timestamp": timestamps[0],
                "end_timestamp": timestamps[-1] + DT,
                "key_timestamp": None,
                "status": None,
                "lateral_decision": None,
                "longitudinal_decision": None,
                "events": ["following"],
                "scenery": None,
                "dynamic_entities": None,
                "justification": None,
                "taxonomy": {"id": "cod-scene", "version": "0.1.1"},
                "raw": None,
            }
            | label("auto", provenance="sample classifier", confidence=0.9)
        ],
        "caption": [
            {
                "token": "caption0",
                "log_token": "log",
                "start_timestamp": timestamps[0],
                "end_timestamp": timestamps[-1],
                "sample_data_token": None,
                "scenario_token": "scenario0",
                "instance_tokens": ["instance_car"],
                "caption_type": "description",
                "text": "The ego vehicle follows a car.",
                "language": "en",
            }
            | label()
        ],
    }


# Manifest fields the writer does not compute (it adds the files, capabilities and t4-devkit).
MANIFEST_INFO = {
    "schema_version": "1.0.0",
    "dataset_id": "sample",
    "version": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "generators": [],
    "annotation_specifications": {},
    "provenance": {
        "rosbag": {
            "log_file_ids": [],
            "storage": None,
            "record_start": "2024-01-01T00:00:00Z",
            "record_end": "2024-01-01T00:00:01Z",
        },
        "topics": {
            "CAM_FRONT": "/sensing/camera/camera0/image_rect_color/compressed",
            "LIDAR_TOP": "/sensing/lidar/concatenated/pointcloud",
        },
        "process_config_id": None,
        "process_config_version_id": None,
    },
    "project_id": None,
    "source_project_id": None,
    "is_synthetic": True,
    "is_discontinuous": None,
    "migrated_from_schema_version": None,
    "migration_notes": None,
}


def write(output_root: Path) -> None:
    """Write the sample dataset to `output_root`, which must not exist."""
    writer = DatasetWriter(output_root)
    camera_video = writer.write_camera("CAM_FRONT", camera_frames(), FPS)
    lidar_path, _ = writer.write_lidar("LIDAR_TOP", lidar_frames(), LIDAR_FIELDS)
    with tempfile.TemporaryDirectory() as tmp:
        map_file = Path(tmp) / "lanelet2_map.osm"
        write_map(map_file)
        writer.copy(map_file, MAP_PATH)
    map_sha256 = hashlib.sha256((output_root / MAP_PATH).read_bytes()).hexdigest()
    records = {
        SchemaName(name): [SCHEMAS.get(SchemaName(name)).from_dict(data) for data in rows]
        for name, rows in tables(camera_video, lidar_path, map_sha256).items()
    }
    writer.save(records, MANIFEST_INFO)


def main() -> None:
    """Write the sample dataset in place of this directory's."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = Path(tmp) / "sample"
        write(output_root)
        for name in ("annotation", "data", "map", "manifest.json"):
            target = ROOT / name
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            shutil.move(output_root / name, target)


if __name__ == "__main__":
    main()
