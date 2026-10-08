"""Generate the T4Dataset 1.0 sample in this directory.

Two keyframes, one camera (CAM_FRONT, AV1) and one LiDAR (LIDAR_TOP, Parquet), and one record
in every optional table. All data is synthetic and deterministic.

Requires an ffmpeg build with libsvtav1, and npx to format JSON with the same prettier version
as pre-commit (so committing does not change the hashes in manifest.json):

    FFMPEG=/path/to/ffmpeg python tests/sample/t4dataset_v1/make_sample_v1.py
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).parent
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
PRETTIER = ["npx", "--yes", "prettier@4.0.0-alpha.8", "--write", "--log-level", "warn"]

NUM_FRAMES = 2
FPS = 10
WIDTH, HEIGHT = 64, 48
NUM_POINTS = 8
T0 = 1704067200000000  # 2024-01-01T00:00:00Z in microseconds
DT = 1_000_000 // FPS

CAMERA_PATH = "data/CAM_FRONT/CAM_FRONT.mp4"
LIDAR_PATH = "data/LIDAR_TOP/LIDAR_TOP.parquet"
MAP_PATH = "map/lanelet2_map.osm"


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    subprocess.run([*PRETTIER, str(path)], check=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_camera() -> None:
    """Encode NUM_FRAMES synthetic RGB frames as intra-only AV1 with pts == frame_index."""
    frames = np.zeros((NUM_FRAMES, HEIGHT, WIDTH, 3), dtype=np.uint8)
    for i in range(NUM_FRAMES):
        frames[i, :, :, 0] = np.linspace(0, 255, WIDTH, dtype=np.uint8)
        frames[i, :, :, 1] = 128 * i
    path = ROOT / CAMERA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    # fmt: off
    cmd = [
        FFMPEG, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS),
        "-i", "-",
        "-c:v", "libsvtav1", "-preset", "6", "-crf", "26", "-g", "1",
        "-svtav1-params", "pred-struct=0:scd=0:film-grain=0:fast-decode=2:lp=0:log-level=1",
        "-pix_fmt", "yuv420p", "-color_range", "pc", "-colorspace", "bt470bg",
        "-color_primaries", "bt709", "-color_trc", "iec61966-2-1",
        "-video_track_timescale", str(FPS), "-movflags", "+faststart",
        "-map_metadata", "-1", "-fflags", "+bitexact",
        str(path),
    ]
    # fmt: on
    subprocess.run(cmd, input=frames.tobytes(), check=True)


def write_lidar() -> None:
    """Write NUM_FRAMES frames of NUM_POINTS points, one row group per frame."""
    rng = np.random.default_rng(0)
    path = ROOT / LIDAR_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = pa.schema(
        [
            ("x", pa.float32()),
            ("y", pa.float32()),
            ("z", pa.float32()),
            ("intensity", pa.float32()),
            ("ring", pa.uint16()),
        ]
    )
    with pq.ParquetWriter(path, schema, compression="zstd") as writer:
        for _ in range(NUM_FRAMES):
            xyzi = rng.uniform(-10, 10, (NUM_POINTS, 4)).astype(np.float32)
            ring = np.arange(NUM_POINTS, dtype=np.uint16)
            table = pa.table(
                [*(pa.array(xyzi[:, k]) for k in range(4)), pa.array(ring)], schema=schema
            )
            writer.write_table(table, row_group_size=NUM_POINTS)


def write_map() -> None:
    path = ROOT / MAP_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((ROOT.parent / "t4dataset" / MAP_PATH).read_bytes())


def label(annotation_type: str = "manual") -> dict:
    return {"annotation_type": annotation_type, "provenance": None, "confidence": None}


def tables() -> dict[str, list[dict]]:
    identity = [1.0, 0.0, 0.0, 0.0]
    zero = [0.0, 0.0, 0.0]
    samples = [f"sample{i}" for i in range(NUM_FRAMES)]
    timestamps = [T0 + i * DT for i in range(NUM_FRAMES)]

    def link(tokens: list[str], i: int) -> dict:
        return {
            "next": tokens[i + 1] if i + 1 < len(tokens) else None,
            "prev": tokens[i - 1] if i > 0 else None,
        }

    sample_data = []
    ego_pose = []
    for channel, sensor, path, fileformat, num_points in (
        ("cam", "sensor_cam", CAMERA_PATH, "av1_mp4", None),
        ("lidar", "sensor_lidar", LIDAR_PATH, "parquet", NUM_POINTS),
    ):
        tokens = [f"{channel}{i}" for i in range(NUM_FRAMES)]
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
                    "is_key_frame": True,
                    "is_valid": True,
                    **link(tokens, i),
                }
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
            {"token": s, "timestamp": timestamps[i], "scene_token": "scene", **link(samples, i)}
            for i, s in enumerate(samples)
        ],
        "sample_data": sample_data,
        "ego_pose": ego_pose,
        "sensor": [
            {
                "token": "sensor_cam",
                "channel": "CAM_FRONT",
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
                    "video": {
                        "path": CAMERA_PATH,
                        "format": "av1_mp4",
                        "codec_profile": "svt-av1 preset6 crf26 intra",
                        "pixel_format": "yuv420p full-range bt601",
                        "bit_depth": 8,
                        "frame_count": NUM_FRAMES,
                        "timescale": FPS,
                    },
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
                "modality": "lidar",
                "translation": [0.0, 0.0, 2.0],
                "rotation": identity,
                "camera": None,
                "lidar": {
                    "container": {
                        "format": "parquet",
                        "path": LIDAR_PATH,
                        "frame_count": NUM_FRAMES,
                        "compression": "zstd",
                    },
                    "fields": [
                        {"name": "x", "dtype": "float32"},
                        {"name": "y", "dtype": "float32"},
                        {"name": "z", "dtype": "float32"},
                        {"name": "intensity", "dtype": "float32"},
                        {"name": "ring", "dtype": "uint16"},
                    ],
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
                "nbr_samples": NUM_FRAMES,
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
                "model": "sample_vehicle",
                "length": 4.9,
                "width": 1.9,
                "height": 2.0,
                "wheel_base": 2.8,
                "rear_axle_to_center": None,
                "sensor_rig_id": None,
                "name": None,
            }
        ],
        "map": [
            {
                "token": "map",
                "log_tokens": ["log"],
                "format": "lanelet2_osm",
                "filename": MAP_PATH,
                "sha256": sha256(ROOT / MAP_PATH),
                "map_id": "sample_map",
                "version_id": "sample_map_version",
                "projector": {
                    "type": "MGRS",
                    "mgrs_grid": "54SUE",
                    "origin": {"lat": None, "lon": None, "alt": None},
                },
                "source": "manual",
                "name": None,
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
                "description": None,
                "index": None,
                "has_orientation": False,
                "has_number": False,
            },
            {
                "token": "category_road",
                "name": "road",
                "description": None,
                "index": None,
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
                "category_token": "category_car",
                "instance_name": "sample::0",
                "nbr_annotations": NUM_FRAMES,
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
                "num_radar_pts": 0,
                **link(sample_annotations, i),
                **label("manual" if i == 0 else "interpolated"),
            }
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
                **label(),
            }
        ],
        "surface_ann": [
            {
                "token": "surface_ann0",
                "sample_data_token": "cam0",
                "category_token": "category_road",
                "mask": {"size": [HEIGHT, WIDTH], "counts": "0"},
                **label(),
            }
        ],
        "keypoint": [
            {
                "token": "keypoint0",
                "sample_data_token": "cam0",
                "instance_token": "instance_car",
                "category_tokens": ["category_car"],
                "keypoints": [[12.0, 18.0]],
                "num_keypoints": 1,
                **label(),
            }
        ],
        "traffic_light": [
            {
                "token": "traffic_light0",
                "timestamp": timestamps[0],
                "regulatory_element_id": 1,
                "elements": [
                    {"color": "green", "shape": "circle", "status": "solid_on", "confidence": 1.0}
                ],
                "object_ann_token": None,
                "instance_token": None,
                **label("auto"),
            }
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
                "segments": [{"preferred_primitive_id": 1, "primitive_ids": [1]}],
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
                **label("auto"),
                "raw": None,
            }
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
                **label(),
            }
        ],
    }


def main() -> None:
    write_camera()
    write_lidar()
    write_map()

    table_entries = {}
    for name, records in tables().items():
        path = ROOT / "annotation" / f"{name}.json"
        write_json(path, records)
        table_entries[name] = {"path": f"annotation/{name}.json", "sha256": sha256(path)}

    assets = [
        {"path": p, "sha256": sha256(ROOT / p), "bytes": (ROOT / p).stat().st_size}
        for p in (CAMERA_PATH, LIDAR_PATH, MAP_PATH)
    ]

    manifest = {
        "schema_version": "1.0.0",
        "dataset_id": "sample",
        "version": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "generators": [{"name": "t4-devkit", "version": "sample"}],
        "capabilities": {
            "tasks": ["detection3d", "detection2d", "segmentation2d", "keypoint", "traffic_light"],
            "modalities": {"camera": ["CAM_FRONT"], "lidar": ["LIDAR_TOP"], "radar": []},
            "map": True,
            "route": True,
            "traffic_light": True,
            "vehicle_state": True,
            "scenario": True,
        },
        "annotation_specifications": {},
        "tables": table_entries,
        "assets": assets,
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
    write_json(ROOT / "manifest.json", manifest)


if __name__ == "__main__":
    main()
