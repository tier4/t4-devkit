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


def render_lanelets(parser: LaneletParser, root_entity: str) -> None:
    """Render lanelet polygons based on relations.

    Args:
        parser (LaneletParser): The LaneletParser instance.
        root_entity (str): The root entity to render.
    """
    for relation in parser.relations.values():
        if relation.tags.get("type") != "lanelet":
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
            subtype = relation.tags.get("subtype", "road")
            if subtype == "road":
                color = LANELET_COLORS["lanelet_road"]
                element_type = "road"
            elif subtype == "crosswalk":
                color = LANELET_COLORS["lanelet_crosswalk"]
                element_type = "crosswalk"
            else:
                color = LANELET_COLORS["lanelet_shoulder"]
                element_type = "shoulder"

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
                elif "light" in subtype:
                    color = LANELET_COLORS["traffic_light"]
                    size = [0.6, 1.2, 0.6]
                    element_type = "light"
                else:
                    color = [0.8, 0.0, 0.8, 0.9]  # Purple
                    size = [0.5, 0.5, 0.5]
                    element_type = "other"

                for i, center in enumerate(coords):
                    entity_path = f"{root_entity}/traffic_elements/{element_type}/{relation.id}_{i}"

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
        elif "road_border" == "subtype":
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
