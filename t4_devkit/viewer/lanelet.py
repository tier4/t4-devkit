from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import rerun as rr

if TYPE_CHECKING:
    from t4_devkit.lanelet import LaneletParser

LANELET_COLORS = {
    # Road markings
    "solid_line": [1.0, 1.0, 1.0, 0.9],  # White
    "dashed_line": [1.0, 1.0, 0.0, 0.8],  # Yellow
    "virtual_line": [0.7, 0.7, 0.7, 0.6],  # Gray
    # Lanelets
    "lanelet_road": [0.3, 0.6, 1.0, 0.4],  # Light blue
    "lanelet_crosswalk": [1.0, 1.0, 0.0, 0.5],  # Yellow
    "lanelet_shoulder": [0.8, 0.6, 1.0, 0.4],  # Purple
    # Infrastructure
    "road_border": [0.2, 0.2, 0.2, 0.9],  # Dark gray
    "curbstone": [0.5, 0.5, 0.5, 0.9],  # Gray
    "traffic_sign": [1.0, 0.2, 0.2, 0.9],  # Red
    "traffic_light": [1.0, 0.6, 0.0, 0.9],  # Orange
    "vegetation": [0.2, 0.8, 0.2, 0.6],  # Green
    "crosswalk": [1.0, 1.0, 0.0, 0.7],  # Yellow
    # Elevation visualization
    "elevation_low": [0.0, 0.0, 1.0, 0.8],  # Blue
    "elevation_high": [1.0, 0.0, 0.0, 0.8],  # Red
}


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


def _traffic_light_kind(way_subtype: str) -> str:
    # red_green -> pedestrian, other (red_yellow_green) -> vehicle
    if way_subtype == "red_green":
        return "pedestrian"
    return "vehicle"


def _traffic_light_mesh(
    center: np.ndarray,
    direction: np.ndarray | None = None,
    *,
    kind: str = "vehicle",
) -> rr.Mesh3D:
    if kind == "pedestrian":
        return _pedestrian_traffic_light_mesh(center, direction)
    return _vehicle_traffic_light_mesh(center, direction)


def _vehicle_traffic_light_mesh(
    center: np.ndarray, direction: np.ndarray | None = None
) -> rr.Mesh3D:
    body_color = [0.05, 0.05, 0.05, 1.0]
    visor_color = [0.02, 0.02, 0.02, 1.0]
    lens_colors = [
        [0.1, 0.9, 0.2, 1.0],
        [1.0, 0.8, 0.1, 1.0],
        [1.0, 0.1, 0.1, 1.0],
    ]

    parts = []
    parts.append(_cuboid_mesh(np.array([0.0, 0.0, 1.0]), (1.8, 0.25, 0.6), body_color))
    parts.append(_cuboid_mesh(np.array([0.0, 0.0, 0.55]), (0.12, 0.12, 0.3), body_color))
    for x_offset, color in zip([-0.55, 0.0, 0.55], lens_colors, strict=True):
        lens_center = np.array([x_offset, -0.13, 1.0])
        parts.append(
            _cuboid_mesh(lens_center + np.array([0.0, -0.02, 0.0]), (0.42, 0.05, 0.42), visor_color)
        )
        parts.append(_disc_mesh(lens_center + np.array([0.0, -0.055, 0.0]), 0.18, color))

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


def _pedestrian_traffic_light_mesh(
    center: np.ndarray,
    direction: np.ndarray | None = None,
) -> rr.Mesh3D:
    body_color = [0.05, 0.05, 0.05, 1.0]
    visor_color = [0.02, 0.02, 0.02, 1.0]
    lens_colors = [
        [1.0, 0.1, 0.1, 1.0],
        [0.1, 0.9, 0.2, 1.0],
    ]

    parts = []
    parts.append(_cuboid_mesh(np.array([0.0, 0.0, 1.0]), (0.55, 0.22, 1.0), body_color))
    parts.append(_cuboid_mesh(np.array([0.0, 0.0, 0.35]), (0.1, 0.1, 0.3), body_color))
    for z_offset, color in zip([1.25, 0.75], lens_colors, strict=True):
        lens_center = np.array([0.0, -0.12, z_offset])
        parts.append(
            _cuboid_mesh(lens_center + np.array([0.0, -0.02, 0.0]), (0.34, 0.05, 0.34), visor_color)
        )
        parts.append(_disc_mesh(lens_center + np.array([0.0, -0.055, 0.0]), 0.14, color))

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


def render_lanelets(parser: LaneletParser, root_entity: str) -> None:
    """Render lanelet polygons based on relations.

    Note that this function only renders lanelets of type "crosswalk".

    Args:
        parser (LaneletParser): The LaneletParser instance.
        root_entity (str): The root entity to render.
    """
    for relation in parser.relations.values():
        if relation.tags.get("type") != "lanelet" or relation.tags.get("subtype") != "crosswalk":
            continue

        left_bound = None
        right_bound = None
        for member in relation.members:
            if member.type == "way" and member.role == "left":
                left_bound = parser.ways.get(member.ref)
            elif member.type == "way" and member.role == "right":
                right_bound = parser.ways.get(member.ref)

        if left_bound and right_bound:
            left_coords = parser.way_coordinates(left_bound)
            right_coords = parser.way_coordinates(right_bound)

            vertices = np.array(left_coords + right_coords[::-1])
            triangles = np.array([(0, i, i + 1) for i in range(1, len(vertices) - 1)])

            color = LANELET_COLORS["lanelet_crosswalk"]
            element_type = "crosswalk"

            entity_path = f"{root_entity}/lanelet/{element_type}/{relation.id}"
            rr.log(
                entity_path,
                rr.Mesh3D(
                    vertex_positions=vertices,
                    triangle_indices=triangles,
                    vertex_colors=[color] * len(vertices),
                ),
                static=True,
            )


def render_traffic_elements(parser: LaneletParser, root_entity: str) -> None:
    """Render traffic signs, lights, and other regulatory elements.

    Args:
        parser (LaneletParser): The lanelet parser.
        root_entity (str): The root entity to render.
    """
    for relation in parser.relations.values():
        if relation.tags.get("type") != "regulatory_element":
            continue

        subtype = relation.tags.get("subtype", "")
        for member in relation.members:
            if member.type == "way" and member.role in ["ref_line", "refers"]:
                way = parser.ways.get(member.ref)
                if not way:
                    continue
                coords = parser.way_coordinates(way)
                if "sign" in subtype:
                    color = LANELET_COLORS["traffic_sign"]
                    size = [0.8, 0.8, 0.8]
                    element_type = "sign"
                elif (
                    "light" in subtype
                    and member.role == "refers"
                    and way.tags.get("type") == "traffic_light"
                ):
                    color = LANELET_COLORS["traffic_light"]
                    size = [0.6, 1.2, 0.6]
                    element_type = "light"
                elif "light" in subtype:
                    continue
                else:
                    color = [0.8, 0.0, 0.8, 0.9]  # Purple
                    size = [0.5, 0.5, 0.5]
                    element_type = "other"

                if element_type == "light":
                    center = np.mean(np.asarray(coords), axis=0)
                    direction = (
                        np.asarray(coords[-1]) - np.asarray(coords[0]) if len(coords) >= 2 else None
                    )
                    kind = _traffic_light_kind(way.tags.get("subtype", ""))
                    entity_path = (
                        f"{root_entity}/traffic_elements/{kind}_light/{relation.id}_{member.ref}"
                    )
                    rr.log(
                        entity_path, _traffic_light_mesh(center, direction, kind=kind), static=True
                    )
                else:
                    for i, center in enumerate(coords):
                        entity_path = (
                            f"{root_entity}/traffic_elements/{element_type}/{relation.id}_{i}"
                        )
                        rr.log(
                            entity_path,
                            rr.Boxes3D(sizes=[size], centers=[center], colors=[color]),
                            static=True,
                        )


def render_ways(parser: LaneletParser, root_entity: str) -> None:
    """Render lanelet ways.

    Args:
        parser (LaneletParser): The lanelet parser.
        root_entity (str): The root entity to render.
    """
    for way in parser.ways.values():
        way_type = way.tags.get("type", "")
        subtype = way.tags.get("subtype", "")

        if not (
            "line_thin" in way_type
            or "line_thick" in way_type
            or "curbstone" in way_type
            or "virtual" == way_type
            or "road_border" == subtype
        ):
            continue

        coords = parser.way_coordinates(way)
        if len(coords) < 2:
            continue

        if "solid" in subtype:
            color = LANELET_COLORS["solid_line"]
            element_type = "road_marking/solid"
        elif "dashed" in subtype:
            color = LANELET_COLORS["dashed_line"]
            element_type = "road_marking/dashed"
        elif "virtual" == way_type:
            color = LANELET_COLORS["virtual_line"]
            element_type = "road_marking/virtual"
        elif "curbstone" == way_type:
            color = LANELET_COLORS["curbstone"]
            element_type = "road_border/curbstone"
        elif "road_border" == subtype:
            color = LANELET_COLORS["road_border"]
            element_type = "road_border/road_border"
        else:
            color = LANELET_COLORS["solid_line"]
            element_type = "road_marking/other"

        entity_path = f"{root_entity}/{element_type}/{way.id}"

        rr.log(
            entity_path,
            rr.LineStrips3D(
                strips=[np.array(coords)],
                colors=[color],
                radii=[0.1 if "thin" in way_type else 0.2],
            ),
            static=True,
        )


def render_geographic_borders(parser: LaneletParser, root_entity: str) -> None:
    """Render road borders on geographical space.

    Args:
        parser (LaneletParser): The LaneletParser object.
        root_entity (str): The root entity path.
    """
    for way in parser.ways.values():
        way_type = way.tags.get("type", "")
        subtype = way.tags.get("subtype", "")

        if not ("curbstone" == way_type or "road_border" == subtype):
            continue

        coords = parser.way_coordinates(way, as_geographic=True)
        lat_lon = np.array([c[:2] for c in coords])
        if len(coords) < 2:
            continue

        color = LANELET_COLORS["road_border"]
        entity_path = f"{root_entity}/{way.id}"

        rr.log(
            entity_path,
            rr.GeoLineStrings(lat_lon=[lat_lon], colors=[color], radii=[2.0]),
            static=True,
        )
