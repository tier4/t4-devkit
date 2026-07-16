from __future__ import annotations

import numpy as np
import rerun as rr

from t4_devkit.lanelet import LaneletParser
from t4_devkit.viewer.lanelet import render_traffic_elements
from t4_devkit.viewer.traffic_light import traffic_light_mesh


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
        traffic_light_mesh(np.array([0.0, 0.0, 0.0])).vertex_positions.as_arrow_array().to_pylist()
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
