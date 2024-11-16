import tempfile
from typing import Any, Generator

import pytest

from t4_devkit.common.io import save_json


# === Attribute ===
@pytest.fixture(scope="module")
def attribute_dict() -> dict:
    """Return a dummy attribute record as dictionary."""
    return {
        "token": "d3262a477673e1306db1791203be81d4",
        "name": "vehicle_state.moving",
        "description": "Is the vehicle moving?",
    }


@pytest.fixture(scope="module")
def attribute_json(attribute_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy attribute record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([attribute_dict], f.name)
        yield f.name


# === CalibratedSensor ===
@pytest.fixture(scope="module")
def calibrated_sensor_dict() -> dict:
    """Return a dummy calibrated sensor record as dictionary."""
    return {
        "token": "16fa3d3ffc292b63027b2547119bbda6",
        "sensor_token": "06f6037f6f687ec0c3b3b3d09cf414a8",
        "translation": [1.0, 1.0, 1.0],
        "rotation": [1.0, 0.0, 0.0, 0.0],
        "camera_intrinsic": [
            [1042.08972, 0.0, 732.18615],
            [0.0, 1044.20679, 547.14188],
            [0.0, 0.0, 1.0],
        ],
        "camera_distortion": [0, 0, 0, 0, 0],
    }


@pytest.fixture(scope="module")
def calibrated_sensor_json(calibrated_sensor_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy calibrated sensor record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([calibrated_sensor_dict], f.name)
        yield f.name


# === Category ===
@pytest.fixture(scope="module")
def category_dict() -> dict:
    """Return a dummy category record as dictionary."""
    return {"token": "49e00f215a71612d94ea3bea48a93402", "name": "animal", "description": ""}


@pytest.fixture(scope="module")
def category_json(category_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy category record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([category_dict], f.name)
        yield f.name


# === EgoPose ===
@pytest.fixture(scope="module")
def ego_pose_dict() -> dict:
    """Return a dummy ego pose record as dictionary."""
    return {
        "token": "d6779d73ac9c5a1f3f372aa182bc8158",
        "translation": [1.0, 1.0, 1.0],
        "rotation": [1.0, 0.0, 0.0, 0.0],
        "timestamp": 1603452042983183,
    }


@pytest.fixture(scope="module")
def ego_pose_json(ego_pose_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy ego pose record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([ego_pose_dict], f.name)
        yield f.name


# === Instance ===
@pytest.fixture(scope="module")
def instance_dict() -> dict:
    """Return a dummy instance record as dictionary."""
    return {
        "token": "77452a485b1986e52b46a2e75349c767",
        "category_token": "fe3f2abcbd5c2f8a23a0b3b2dd57f999",
        "instance_name": "",
        "nbr_annotations": 88,
        "first_annotation_token": "f1cf0a8729de7b30742f1e55c2926ea2",
        "last_annotation_token": "ad79c1b987cb82a113d1e506a249f98b",
    }


@pytest.fixture(scope="module")
def instance_json(instance_dict) -> dict:
    """Return a file path of dummy instance record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([instance_dict], f.name)
        yield f.name


# === Log ===
@pytest.fixture(scope="module")
def log_dict() -> dict:
    """Return a dummy log record as dictionary."""
    return {
        "token": "daacef1242fcfba3bba54c81ee684bba",
        "logfile": "",
        "vehicle": "xx1",
        "data_captured": "",
        "location": "lidar_cuboid_odaiba_2hz",
    }


@pytest.fixture(scope="module")
def log_json(log_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy log record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([log_dict], f.name)
        yield f.name


# === Map ===
@pytest.fixture(scope="module")
def map_dict() -> dict:
    """Return a dummy map record as dictionary."""
    return {
        "token": "134e917e0c5404184ff04997da7b7e79",
        "log_tokens": ["daacef1242fcfba3bba54c81ee684bba"],
        "category": "",
        "filename": "",
    }


@pytest.fixture(scope="module")
def map_json(map_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy map record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([map_dict], f.name)
        yield f.name


# === SampleAnnotation ===
@pytest.fixture(scope="module")
def sample_annotation_dict() -> dict:
    """Return a dummy sample annotation record as dictionary."""
    return {
        "token": "f1cf0a8729de7b30742f1e55c2926ea2",
        "sample_token": "6026254f0d08f8001755d222_0000",
        "instance_token": "77452a485b1986e52b46a2e75349c767",
        "attribute_tokens": ["d3262a477673e1306db1791203be81d4"],
        "visibility_token": "1",
        "translation": [1.0, 1.0, 1.0],
        "size": [1.0, 1.0, 1.0],
        "rotation": [1.0, 0.0, 0.0, 0.0],
        "num_lidar_pts": 3022,
        "num_radar_pts": 0,
        "next": "7b0ae1dae7531b7b917f403cb22259e6",
        "prev": "",
    }


@pytest.fixture(scope="module")
def sample_annotation_json(sample_annotation_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy sample annotation record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([sample_annotation_dict], f.name)
        yield f.name


# === Sample ===
@pytest.fixture(scope="module")
def sample_dict() -> dict:
    """Return a dummy sample record as dictionary."""
    return {
        "token": "6026254f0d08f8001755d222_0000",
        "timestamp": 1603452043175691,
        "scene_token": "6026254f0d08f8001755d222",
        "next": "6026254f0d08f8001755d222_0001",
        "prev": "",
    }


@pytest.fixture(scope="module")
def sample_json(sample_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy sample record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([sample_dict], f.name)
        yield f.name


# === SampleData ===
@pytest.fixture(scope="module")
def sample_data_dict() -> dict:
    """Return a dummy sample data record as dictionary."""
    return {
        "token": "df2bee5733d8607e49bf792fac3014a3",
        "sample_token": "6026254f0d08f8001755d222_0000",
        "ego_pose_token": "d6779d73ac9c5a1f3f372aa182bc8158",
        "calibrated_sensor_token": "0c434d5a27ef0404331549435b9861e4",
        "filename": "data/camera/0.jpg",
        "fileformat": "jpg",
        "width": 1440,
        "height": 1080,
        "timestamp": 1603452042983183,
        "is_key_frame": False,
        "next": "efe096cc01a610af846c29aaf4decc9a",
        "prev": "",
    }


@pytest.fixture(scope="module")
def sample_data_json(sample_data_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy sample data record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([sample_data_dict], f.name)
        yield f.name


# === Scene ===
@pytest.fixture(scope="module")
def scene_dict() -> dict:
    """Return a dummy scene record as dictionary."""
    return {
        "token": "6026254f0d08f8001755d222",
        "name": "test",
        "description": "",
        "log_token": "daacef1242fcfba3bba54c81ee684bba",
        "nbr_samples": 88,
        "first_sample_token": "6026254f0d08f8001755d222_0000",
        "last_sample_token": "6026254f0d08f8001755d222_0000",
    }


@pytest.fixture(scope="module")
def scene_json(scene_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy scene record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([scene_dict], f.name)
        yield f.name


# === Sensor ===
@pytest.fixture(scope="module")
def sensor_dict() -> dict:
    """Return a dummy sensor record as dictionary."""
    return {
        "token": "68d53dc0e128547e4d92c47de63742af",
        "channel": "LIDAR_CONCAT",
        "modality": "lidar",
    }


@pytest.fixture(scope="module")
def sensor_json(sensor_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy sensor record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([sensor_dict], f.name)
        yield f.name


# === Visibility ===
@pytest.fixture(scope="module")
def visibility_dict() -> dict:
    """Return a dummy visibility record as dictionary."""
    return {
        "description": "visibility of whole object is between 0 and 40%",
        "token": "1",
        "level": "v0-40",
    }


@pytest.fixture(scope="module")
def visibility_json(visibility_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy visibility record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([visibility_dict], f.name)
        yield f.name


# === ObjectAnn ===
@pytest.fixture(scope="module")
def object_ann_dict() -> dict:
    """Return a dummy object ann as dictionary."""
    return {
        "token": "4230e00708fb3f404d246ea97716f848",
        "sample_data_token": "a1d3257e11ec9d4a587ea7053b33f1c1",
        "instance_token": "8f37d145617ec022386982a2b43f1539",
        "category_token": "7864884179fb37bf9e973016b13a332c",
        "attribute_tokens": [],
        "bbox": [0, 408.0529355733727, 1920, 728.1832152454293],
        "mask": {"size": [1920, 1280], "counts": "UFBQWzI='"},
    }


@pytest.fixture(scope="module")
def object_ann_json(object_ann_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy object ann record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([object_ann_dict], f.name)
        yield f.name


# === SurfaceAnn ===
@pytest.fixture(scope="module")
def surface_ann_dict() -> dict:
    """Return a dummy surface ann as dictionary."""
    return {
        "token": "4230e00708fb3f404d246ea97716f848",
        "sample_data_token": "a1d3257e11ec9d4a587ea7053b33f1c1",
        "category_token": "7864884179fb37bf9e973016b13a332c",
        "mask": {"size": [1920, 1280], "counts": "UFBQWzI='"},
    }


@pytest.fixture(scope="module")
def surface_ann_json(surface_ann_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy surface ann record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([surface_ann_dict], f.name)
        yield f.name


# === VehicleState ===
@pytest.fixture(scope="module")
def vehicle_state_dict() -> dict:
    """Return a dummy vehicle state as dictionary."""
    return {
        "token": "269572c280bd5cf9630ca542e6a60185",
        "timestamp": 1724306784277396,
        "accel_pedal": 0.0,
        "brake_pedal": 1.0,
        "steer_pedal": 0.6063521901837905,
        "steering_tire_angle": 0.6063522100448608,
        "steering_wheel_angle": 9.291000366210938,
        "shift_state": "PARK",
        "indicators": {"left": "off", "right": "on", "hazard": "off"},
        "additional_info": {"speed": 0.0},
    }


@pytest.fixture(scope="module")
def vehicle_state_json(vehicle_state_dict) -> Generator[str, Any, None]:
    """Return a file path of dummy vehicle state record."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_json([vehicle_state_dict], f.name)
        yield f.name
