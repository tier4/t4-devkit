from __future__ import annotations

import numpy as np
import rerun as rr
from pyquaternion import Quaternion

from t4_devkit.dataclass import LidarPointCloud
from t4_devkit.lanelet import LaneletParser
from t4_devkit.schema import CalibratedSensor, EgoPose, Sensor
from t4_devkit.viewer import EntityPath, format_entity
from t4_devkit.viewer.lanelet import _traffic_light_mesh, render_traffic_elements


def test_format_entity() -> None:
    """Test `format_entity(...)` function."""
    assert "map" == format_entity("map")
    assert "map/base_link" == format_entity("map", "base_link")
    assert "map/base_link" == format_entity("map", "map/base_link")
    assert "map/base_link/camera" == format_entity("map", "map/base_link", "camera")
    assert "map/base_link/camera" == format_entity("map", "map/base_link", "base_link/camera")
    assert "map/base_link" == format_entity(EntityPath.MAP, EntityPath.BASE_LINK)
    assert "map/base_link/camera" == format_entity(EntityPath.MAP, EntityPath.BASE_LINK, "camera")


def test_render_box3ds(dummy_viewer, dummy_box3ds) -> None:
    """Test rendering 3D boxes with `RerunViewer`."""
    seconds = 1.0  # [sec]
    frame_id = "map"

    dummy_viewer.render_box3ds(seconds, dummy_box3ds)

    centers = [box.position for box in dummy_box3ds]
    rotations = [box.rotation for box in dummy_box3ds]
    sizes = [box.size for box in dummy_box3ds]
    class_ids = [dummy_viewer.label2id[box.semantic_label.name] for box in dummy_box3ds]
    velocities = [box.velocity for box in dummy_box3ds]
    uuids = [box.uuid for box in dummy_box3ds]

    dummy_viewer.render_box3ds(
        seconds,
        frame_id=frame_id,
        centers=centers,
        rotations=rotations,
        sizes=sizes,
        class_ids=class_ids,
        velocities=velocities,
        uuids=uuids,
    )


def test_render_box2ds(dummy_viewer, dummy_box2ds) -> None:
    """Test rendering 2D boxes with `RerunViewer`."""
    seconds = 1.0  # [sec]

    dummy_viewer.render_box2ds(seconds, dummy_box2ds)

    camera = "camera"
    rois = [box.roi for box in dummy_box2ds]
    class_ids = [dummy_viewer.label2id[box.semantic_label.name] for box in dummy_box2ds]
    uuids = [box.uuid for box in dummy_box2ds]

    dummy_viewer.render_box2ds(seconds, camera=camera, rois=rois, class_ids=class_ids, uuids=uuids)


def test_render_segmentation2d(dummy_viewer, dummy_camera_calibration) -> None:
    """Test rendering 2D segmentation mask with `RerunViewer`."""
    seconds = 1.0  # [sec]

    (width, height), _ = dummy_camera_calibration

    camera = "camera"
    masks = [np.zeros((height, width), dtype=np.uint8) for _ in range(2)]
    masks[0][0:100, 0:100] = 1
    masks[1][200:300, 200:300] = 1
    class_ids = [1, 2]

    dummy_viewer.render_segmentation2d(seconds, camera=camera, masks=masks, class_ids=class_ids)


def test_render_pointcloud(dummy_viewer) -> None:
    """Test rendering pointcloud with `RerunViewer`."""
    seconds = 1.0  # [sec]

    dummy_pointcloud = LidarPointCloud(np.random.rand(4, 100))
    dummy_viewer.render_pointcloud(seconds, "lidar", dummy_pointcloud)


def test_render_image(dummy_viewer, dummy_camera_calibration) -> None:
    """Test rendering image with `RerunViewer`."""
    seconds = 1.0  # [sec]

    (width, height), _ = dummy_camera_calibration
    dummy_image = np.zeros((height, width, 3), dtype=np.uint8)
    dummy_viewer.render_image(seconds=seconds, camera="camera", image=dummy_image)


def test_render_ego(dummy_viewer) -> None:
    """Test rendering ego pose with `RerunViewer`."""
    seconds = 1.0  # [sec]

    # without `EgoPose`
    translation = [1, 0, 0]
    rotation = Quaternion([1, 0, 0, 0])
    dummy_viewer.render_ego(seconds, translation=translation, rotation=rotation)

    # with `EgoPose`
    ego_pose = EgoPose(
        token="ego",
        translation=translation,
        rotation=rotation,
        timestamp=int(1e6),
    )
    dummy_viewer.render_ego(ego_pose)


def test_render_calibration(dummy_viewer, dummy_camera_calibration) -> None:
    """Test rendering sensor calibration with `RerunViewer`."""
    # without `Sensor` and `CalibratedSensor`
    channel = "camera"
    modality = "camera"
    translation = [1, 1, 1]
    rotation = Quaternion([1, 0, 0, 0])
    _, camera_intrinsic = dummy_camera_calibration
    dummy_viewer.render_calibration(
        channel=channel,
        modality=modality,
        translation=translation,
        rotation=rotation,
        camera_intrinsic=camera_intrinsic,
    )

    # with `Sensor` and `CalibratedSensor`
    sensor = Sensor(token="sensor", channel="camera", modality="camera")
    calibration = CalibratedSensor(
        token="sensor_calibration",
        sensor_token="sensor",
        translation=translation,
        rotation=rotation,
        camera_intrinsic=camera_intrinsic,
        camera_distortion=[0, 0, 0, 0, 0],
    )
    dummy_viewer.render_calibration(sensor, calibration)


def test_render_map(dummy_viewer, dummy_lanelet_path) -> None:
    """Test rendering map with `RerunViewer`."""
    dummy_viewer.render_map(dummy_lanelet_path)


def test_render_map_traffic_light_as_mesh(tmp_path, monkeypatch) -> None:
    """Test rendering traffic light positions as meshes."""
    lanelet_path = tmp_path / "lanelet2_map.osm"
    lanelet_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="35.0" lon="139.0" ele="1.0">
    <tag k="local_x" v="10.0"/>
    <tag k="local_y" v="20.0"/>
    <tag k="ele" v="1.0"/>
  </node>
  <node id="2" lat="35.0" lon="139.0" ele="1.0">
    <tag k="local_x" v="10.0"/>
    <tag k="local_y" v="22.0"/>
    <tag k="ele" v="1.0"/>
  </node>
  <node id="3" lat="35.0" lon="139.0" ele="1.0">
    <tag k="local_x" v="20.0"/>
    <tag k="local_y" v="20.0"/>
    <tag k="ele" v="1.0"/>
  </node>
  <node id="4" lat="35.0" lon="139.0" ele="1.0">
    <tag k="local_x" v="21.0"/>
    <tag k="local_y" v="20.0"/>
    <tag k="ele" v="1.0"/>
  </node>
  <way id="100">
    <nd ref="1"/>
    <nd ref="2"/>
    <tag k="type" v="traffic_light"/>
    <tag k="subtype" v="red_yellow_green"/>
  </way>
  <way id="101">
    <nd ref="3"/>
    <nd ref="4"/>
    <tag k="type" v="traffic_light"/>
    <tag k="subtype" v="red_green"/>
  </way>
  <relation id="200">
    <member type="way" ref="100" role="refers"/>
    <tag k="type" v="regulatory_element"/>
    <tag k="subtype" v="traffic_light"/>
  </relation>
  <relation id="201">
    <member type="way" ref="101" role="refers"/>
    <tag k="type" v="regulatory_element"/>
    <tag k="subtype" v="traffic_light"/>
  </relation>
</osm>
""",
        encoding="utf-8",
    )

    logs = []

    def log(entity_path, entity, *, static=False):
        logs.append((entity_path, entity, static))

    monkeypatch.setattr("t4_devkit.viewer.lanelet.rr.log", log)

    render_traffic_elements(LaneletParser(str(lanelet_path)), "map/vector_map")

    assert len(logs) == 2
    entities = {entity_path: entity for entity_path, entity, _ in logs}
    assert set(entities) == {
        "map/vector_map/traffic_elements/vehicle_light/200_100",
        "map/vector_map/traffic_elements/pedestrian_light/201_101",
    }
    assert all(isinstance(entity, rr.Mesh3D) for entity in entities.values())
    assert all(static is True for _, _, static in logs)

    default_vertices = np.array(
        _traffic_light_mesh(np.array([0.0, 0.0, 0.0])).vertex_positions.as_arrow_array().to_pylist()
    )
    default_span = default_vertices.max(axis=0) - default_vertices.min(axis=0)
    assert default_span[0] > default_span[2]
    assert len(default_vertices) > 100

    vehicle_vertices = np.array(
        entities["map/vector_map/traffic_elements/vehicle_light/200_100"]
        .vertex_positions.as_arrow_array()
        .to_pylist()
    )
    vehicle_span = vehicle_vertices.max(axis=0) - vehicle_vertices.min(axis=0)
    assert vehicle_span[1] > vehicle_span[0]

    pedestrian_vertices = np.array(
        entities["map/vector_map/traffic_elements/pedestrian_light/201_101"]
        .vertex_positions.as_arrow_array()
        .to_pylist()
    )
    pedestrian_span = pedestrian_vertices.max(axis=0) - pedestrian_vertices.min(axis=0)
    assert pedestrian_span[2] > pedestrian_span[0]
