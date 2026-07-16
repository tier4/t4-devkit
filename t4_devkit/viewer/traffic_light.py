from __future__ import annotations

import numpy as np
import rerun as rr

from t4_devkit.schema import TrafficLightElementColor, TrafficLightElementShape, TrafficLightElement

__all__ = ["traffic_light_kind", "traffic_light_mesh"]

LENS_COLORS = {
    TrafficLightElementColor.GREEN: [0.1, 0.9, 0.2],
    TrafficLightElementColor.AMBER: [1.0, 0.8, 0.1],
    TrafficLightElementColor.RED: [1.0, 0.1, 0.1],
}
INACTIVE_LENS_RGB_SCALE = 0.12


def traffic_light_kind(way_subtype: str) -> str:
    if way_subtype == "red_green":
        return "pedestrian"
    return "vehicle"


def traffic_light_mesh(
    center: np.ndarray,
    direction: np.ndarray | None = None,
    *,
    kind: str = "vehicle",
    elements: list[TrafficLightElement] | None = None,
) -> rr.Mesh3D:
    if kind == "pedestrian":
        return _pedestrian_traffic_light_mesh(center, direction, elements)
    return _vehicle_traffic_light_mesh(center, direction, elements)


def _cuboid_mesh(
    center: np.ndarray,
    size: tuple[float, float, float],
    color: list[float],
) -> tuple[np.ndarray, np.ndarray, list[list[float]]]:
    half_size = np.asarray(size, dtype=float) / 2.0
    offsets = np.array(
        [
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1],
        ],
        dtype=float,
    )
    vertices = center + offsets * half_size
    triangles = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [4, 6, 5],
            [4, 7, 6],
            [0, 4, 5],
            [0, 5, 1],
            [1, 5, 6],
            [1, 6, 2],
            [2, 6, 7],
            [2, 7, 3],
            [3, 7, 4],
            [3, 4, 0],
        ],
        dtype=np.uint32,
    )
    colors = [color] * len(vertices)
    return vertices, triangles, colors


def _disc_mesh(
    center: np.ndarray,
    radius: float,
    color: list[float],
    *,
    segments: int = 24,
) -> tuple[np.ndarray, np.ndarray, list[list[float]]]:
    angles = np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False)
    vertices = np.vstack(
        [
            center,
            np.column_stack(
                [
                    center[0] + radius * np.cos(angles),
                    np.full(segments, center[1]),
                    center[2] + radius * np.sin(angles),
                ]
            ),
        ]
    )
    triangles = np.array(
        [[0, i, 1 + (i % segments)] for i in range(1, segments + 1)],
        dtype=np.uint32,
    )
    colors = [color] * len(vertices)
    return vertices, triangles, colors


def _orient_vertices(
    vertices: np.ndarray,
    center: np.ndarray,
    direction: np.ndarray | None,
) -> np.ndarray:
    if direction is None:
        return vertices + center

    x_axis = np.array([direction[0], direction[1], 0.0], dtype=float)
    norm = np.linalg.norm(x_axis)
    if norm == 0.0:
        return vertices + center

    x_axis /= norm
    z_axis = np.array([0.0, 0.0, 1.0])
    y_axis = np.cross(z_axis, x_axis)
    rotation = np.column_stack([x_axis, y_axis, z_axis])
    return vertices @ rotation.T + center


def _vehicle_traffic_light_mesh(
    center: np.ndarray,
    direction: np.ndarray | None = None,
    elements: list[TrafficLightElement] | None = None,
) -> rr.Mesh3D:
    body_color = [0.05, 0.05, 0.05, 1.0]
    visor_color = [0.02, 0.02, 0.02, 1.0]
    lens_names = [
        TrafficLightElementColor.GREEN,
        TrafficLightElementColor.AMBER,
        TrafficLightElementColor.RED,
    ]
    active_color = _circle_element_color(elements)

    parts = []
    # add body
    parts.append(_cuboid_mesh(np.array([0.0, 0.0, 1.0]), (1.8, 0.25, 0.6), body_color))
    # add lens (green, amber, red)
    for x_offset, lens_name in zip([-0.55, 0.0, 0.55], lens_names, strict=True):
        lens_center = np.array([x_offset, -0.13, 1.0])
        parts.append(
            _cuboid_mesh(
                lens_center + np.array([0.0, -0.02, 0.0]),
                (0.42, 0.05, 0.42),
                visor_color,
            )
        )
        parts.append(
            _disc_mesh(
                lens_center + np.array([0.0, -0.055, 0.0]),
                0.18,
                _lens_color(lens_name, active_color),
            )
        )

    return _combine_mesh_parts(parts, center, direction)


def _pedestrian_traffic_light_mesh(
    center: np.ndarray,
    direction: np.ndarray | None = None,
    elements: list[TrafficLightElement] | None = None,
) -> rr.Mesh3D:
    body_color = [0.05, 0.05, 0.05, 1.0]
    visor_color = [0.02, 0.02, 0.02, 1.0]
    lens_names = [TrafficLightElementColor.RED, TrafficLightElementColor.GREEN]
    active_color = _circle_element_color(elements)

    parts = []
    # add body
    parts.append(_cuboid_mesh(np.array([0.0, 0.0, 1.0]), (0.55, 0.22, 1.0), body_color))
    # add lens (red, green)
    for z_offset, lens_name in zip([1.25, 0.75], lens_names, strict=True):
        lens_center = np.array([0.0, -0.12, z_offset])
        parts.append(
            _cuboid_mesh(
                lens_center + np.array([0.0, -0.02, 0.0]),
                (0.34, 0.05, 0.34),
                visor_color,
            )
        )
        parts.append(
            _disc_mesh(
                lens_center + np.array([0.0, -0.055, 0.0]),
                0.14,
                _lens_color(lens_name, active_color),
            )
        )

    return _combine_mesh_parts(parts, center, direction)


def _circle_element_color(
    elements: list[TrafficLightElement] | None,
) -> TrafficLightElementColor | None:
    if elements is None:
        return None

    for element in elements:
        if element.shape == TrafficLightElementShape.CIRCLE:
            return element.color
    return None


def _lens_color(
    lens_name: TrafficLightElementColor,
    active_color: TrafficLightElementColor | None,
) -> list[float]:
    if active_color is None:
        return _inactive_lens_color(lens_name)

    if active_color == lens_name:
        return _active_lens_color(lens_name)
    return _inactive_lens_color(lens_name)


def _active_lens_color(lens_name: TrafficLightElementColor) -> list[float]:
    return LENS_COLORS[lens_name]


def _inactive_lens_color(lens_name: TrafficLightElementColor) -> list[float]:
    return [component * INACTIVE_LENS_RGB_SCALE for component in LENS_COLORS[lens_name]]


def _combine_mesh_parts(
    parts: list[tuple[np.ndarray, np.ndarray, list[list[float]]]],
    center: np.ndarray,
    direction: np.ndarray | None,
) -> rr.Mesh3D:
    vertices = []
    triangles = []
    colors = []
    vertex_offset = 0
    for part_vertices, part_triangles, part_colors in parts:
        vertices.append(part_vertices)
        triangles.append(part_triangles + vertex_offset)
        colors.extend(part_colors)
        vertex_offset += len(part_vertices)

    return rr.Mesh3D(
        vertex_positions=_orient_vertices(np.vstack(vertices), center, direction),
        triangle_indices=np.vstack(triangles),
        vertex_colors=colors,
    )
