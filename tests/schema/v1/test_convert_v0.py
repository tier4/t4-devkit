from __future__ import annotations

from pathlib import Path

from t4_devkit.schema.v1 import V0_FALLBACKS, SchemaName, load_dataset

SAMPLE_V0 = Path(__file__).parents[2] / "sample" / "t4dataset"


def test_load_v0_dataset() -> None:
    """A 0.x dataset loads as 1.0 records, with placeholders for what 0.x never stored."""
    dataset = load_dataset(SAMPLE_V0)
    tables = dataset.tables

    assert dataset.manifest is None
    assert len(tables[SchemaName.SAMPLE]) == 3
    assert len(tables[SchemaName.SAMPLE_DATA]) == 9

    # calibrated_sensor rows become sensor rows with the same tokens
    sensors = {sensor.channel: sensor for sensor in tables[SchemaName.SENSOR]}
    assert sorted(sensor.index for sensor in sensors.values()) == [0, 1, 2]
    camera = sensors["CAM_FRONT"].camera
    assert (camera.width, camera.height) == (800, 600)
    assert camera.distortion_model == "plumb_bob"
    lidar = sensors["LIDAR_TOP"].lidar
    assert lidar.container.format == "bin"
    assert lidar.container.frame_count == 3
    assert [field.name for field in lidar.fields] == ["x", "y", "z", "intensity", "channel"]
    for record in tables[SchemaName.SAMPLE_DATA]:
        assert dataset.get(SchemaName.SENSOR, record.sensor_token).channel in sensors
        assert record.frame_index is None

    # log -> vehicle (placeholders) and map (hash from the file)
    log = tables[SchemaName.LOG][0]
    vehicle = dataset.get(SchemaName.VEHICLE, log.vehicle_token)
    assert vehicle.name == "test_vehicle"
    assert vehicle.model == V0_FALLBACKS["vehicle"]["model"]
    map_ = dataset.get(SchemaName.MAP, log.map_token)
    assert map_.map_id == V0_FALLBACKS["map"]["map_id"]
    assert len(map_.sha256) == 64
