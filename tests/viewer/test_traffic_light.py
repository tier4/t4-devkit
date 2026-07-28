from __future__ import annotations

import numpy as np
import rerun as rr

from t4_devkit.lanelet import LaneletParser
from t4_devkit.schema import TrafficLightElementColor, TrafficLightElementShape, TrafficLightElement
from t4_devkit.viewer.lanelet import render_traffic_elements
from t4_devkit.viewer.traffic_light import (
    _active_lens_color,
    _inactive_lens_color,
    traffic_light_mesh,
)


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
  <relation id="300">
    <member type="way" ref="100" role="left"/>
    <member type="way" ref="101" role="right"/>
    <member type="relation" ref="200" role="regulatory_element"/>
    <tag k="type" v="lanelet"/>
    <tag k="subtype" v="road"/>
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
    default_colors = (
        traffic_light_mesh(np.array([0.0, 0.0, 0.0])).vertex_colors.as_arrow_array().to_pylist()
    )
    default_span = default_vertices.max(axis=0) - default_vertices.min(axis=0)
    assert default_span[0] > default_span[2]
    assert len(default_vertices) > 100
    assert _active_lens_color_value(TrafficLightElementColor.GREEN) not in default_colors
    assert _active_lens_color_value(TrafficLightElementColor.AMBER) not in default_colors
    assert _active_lens_color_value(TrafficLightElementColor.RED) not in default_colors

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


def test_render_map_traffic_light_color_from_lane_connector(tmp_path, monkeypatch) -> None:
    """Test rendering traffic light color from lane connector elements."""
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
  <way id="100">
    <nd ref="1"/>
    <nd ref="2"/>
    <tag k="type" v="traffic_light"/>
    <tag k="subtype" v="red_yellow_green"/>
  </way>
  <relation id="200">
    <member type="way" ref="100" role="refers"/>
    <tag k="type" v="regulatory_element"/>
    <tag k="subtype" v="traffic_light"/>
  </relation>
  <relation id="300">
    <member type="way" ref="100" role="left"/>
    <member type="way" ref="100" role="right"/>
    <member type="relation" ref="200" role="regulatory_element"/>
    <tag k="type" v="lanelet"/>
    <tag k="subtype" v="road"/>
  </relation>
</osm>
""",
        encoding="utf-8",
    )

    logs = []

    def log(entity_path, entity, *, static=False):
        logs.append((entity_path, entity, static))

    monkeypatch.setattr("t4_devkit.viewer.lanelet.rr.log", log)

    render_traffic_elements(
        LaneletParser(str(lanelet_path)),
        "map/vector_map",
        traffic_light_elements={
            "300": [
                TrafficLightElement(
                    color=TrafficLightElementColor.RED,
                    shape=TrafficLightElementShape.CIRCLE,
                ),
                TrafficLightElement(
                    color=TrafficLightElementColor.GREEN,
                    shape=TrafficLightElementShape.UP_LEFT_ARROW,
                ),
            ]
        },
        traffic_lights_static=False,
    )

    assert len(logs) == 1
    entity_path, entity, static = logs[0]
    assert entity_path == "map/vector_map/traffic_elements/vehicle_light/200_100"
    assert isinstance(entity, rr.Mesh3D)
    assert static is False

    colors = entity.vertex_colors.as_arrow_array().to_pylist()
    assert _active_lens_color_value(TrafficLightElementColor.RED) in colors
    assert _active_lens_color_value(TrafficLightElementColor.GREEN) not in colors
    assert _active_lens_color_value(TrafficLightElementColor.AMBER) not in colors

    vertices = entity.vertex_positions.as_arrow_array().to_pylist()
    circle_only_vertices = (
        traffic_light_mesh(
            np.array([0.0, 0.0, 0.0]),
            elements=[
                TrafficLightElement(
                    color=TrafficLightElementColor.RED,
                    shape=TrafficLightElementShape.CIRCLE,
                )
            ],
        )
        .vertex_positions.as_arrow_array()
        .to_pylist()
    )
    assert len(vertices) == len(circle_only_vertices)


def test_traffic_light_ignores_non_circle_elements() -> None:
    """Test non-circle elements do not create additional meshes."""
    circle_only = traffic_light_mesh(
        np.array([0.0, 0.0, 0.0]),
        elements=[
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.CIRCLE,
            )
        ],
    )
    with_non_circle_elements = traffic_light_mesh(
        np.array([0.0, 0.0, 0.0]),
        elements=[
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.CIRCLE,
            ),
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.LEFT_ARROW,
            ),
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.UP_RIGHT_ARROW,
            ),
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.CROSS,
            ),
        ],
    )

    circle_only_vertices = circle_only.vertex_positions.as_arrow_array().to_pylist()
    non_circle_vertices = with_non_circle_elements.vertex_positions.as_arrow_array().to_pylist()
    assert len(non_circle_vertices) == len(circle_only_vertices)


def test_pedestrian_traffic_light_ignores_non_circle_elements() -> None:
    """Test pedestrian traffic lights ignore non-circle elements."""
    circle_only = traffic_light_mesh(
        np.array([0.0, 0.0, 0.0]),
        kind="pedestrian",
        elements=[
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.CIRCLE,
            ),
        ],
    )
    with_non_circle_element = traffic_light_mesh(
        np.array([0.0, 0.0, 0.0]),
        kind="pedestrian",
        elements=[
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.CIRCLE,
            ),
            TrafficLightElement(
                color=TrafficLightElementColor.GREEN,
                shape=TrafficLightElementShape.LEFT_ARROW,
            ),
        ],
    )

    circle_only_vertices = circle_only.vertex_positions.as_arrow_array().to_pylist()
    non_circle_vertices = with_non_circle_element.vertex_positions.as_arrow_array().to_pylist()
    assert len(non_circle_vertices) == len(circle_only_vertices)


def test_inactive_lens_color_is_dimmed() -> None:
    """Test inactive lens colors are visually dimmed by RGB scaling."""
    active_color = _active_lens_color(TrafficLightElementColor.GREEN)
    inactive_color = _inactive_lens_color(TrafficLightElementColor.GREEN)

    assert inactive_color[0] < active_color[0]
    assert inactive_color[1] < active_color[1]
    assert inactive_color[2] < active_color[2]


def _active_lens_color_value(color: TrafficLightElementColor) -> int:
    inactive_colors = set(
        traffic_light_mesh(
            np.array([0.0, 0.0, 0.0]),
            elements=[
                TrafficLightElement(
                    color=TrafficLightElementColor.UNKNOWN,
                    shape=TrafficLightElementShape.CIRCLE,
                )
            ],
        )
        .vertex_colors.as_arrow_array()
        .to_pylist()
    )
    active_colors = set(
        traffic_light_mesh(
            np.array([0.0, 0.0, 0.0]),
            elements=[
                TrafficLightElement(
                    color=color,
                    shape=TrafficLightElementShape.CIRCLE,
                )
            ],
        )
        .vertex_colors.as_arrow_array()
        .to_pylist()
    )
    lens_colors = active_colors - inactive_colors
    assert len(lens_colors) == 1
    return lens_colors.pop()
