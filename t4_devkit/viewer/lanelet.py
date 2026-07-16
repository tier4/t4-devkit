from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

import numpy as np
import rerun as rr

from t4_devkit.schema import TrafficLightElement

from .traffic_light import traffic_light_kind, traffic_light_mesh

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


def render_traffic_elements(
    parser: LaneletParser,
    root_entity: str,
    *,
    traffic_light_elements: Mapping[str, list[TrafficLightElement]] | None = None,
    traffic_lights_static: bool = True,
    render_traffic_lights: bool = True,
    render_other_elements: bool = True,
) -> None:
    """Render traffic signs, lights, and other regulatory elements.

    Args:
        parser (LaneletParser): The lanelet parser.
        root_entity (str): The root entity to render.
        traffic_light_elements (Mapping[str, list[TrafficLightElement]] | None, optional):
            Mapping from lane connector IDs to traffic light elements.
        traffic_lights_static (bool, optional): Whether to log traffic light meshes as static.
        render_traffic_lights (bool, optional): Whether to render traffic light meshes.
        render_other_elements (bool, optional): Whether to render non-traffic-light elements.
    """
    traffic_light_regulatory_to_lanelet_ids = _traffic_light_regulatory_to_lanelet_ids(parser)

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
                is_traffic_light = (
                    "light" in subtype
                    and member.role == "refers"
                    and way.tags.get("type") == "traffic_light"
                )
                if "sign" in subtype:
                    color = LANELET_COLORS["traffic_sign"]
                    size = [0.8, 0.8, 0.8]
                    element_type = "sign"
                elif is_traffic_light:
                    if not render_traffic_lights:
                        continue
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
                    kind = traffic_light_kind(way.tags.get("subtype", ""))
                    entity_path = (
                        f"{root_entity}/traffic_elements/{kind}_light/{relation.id}_{member.ref}"
                    )
                    elements = _traffic_light_element(
                        relation.id,
                        traffic_light_elements,
                        traffic_light_regulatory_to_lanelet_ids,
                    )
                    rr.log(
                        entity_path,
                        traffic_light_mesh(
                            center,
                            direction,
                            kind=kind,
                            elements=elements,
                        ),
                        static=traffic_lights_static,
                    )
                else:
                    if not render_other_elements:
                        continue
                    for i, center in enumerate(coords):
                        entity_path = (
                            f"{root_entity}/traffic_elements/{element_type}/{relation.id}_{i}"
                        )
                        rr.log(
                            entity_path,
                            rr.Boxes3D(sizes=[size], centers=[center], colors=[color]),
                            static=True,
                        )


def _traffic_light_regulatory_to_lanelet_ids(parser: LaneletParser) -> dict[str, set[str]]:
    output: dict[str, set[str]] = {}
    for relation in parser.relations.values():
        if relation.tags.get("type") != "lanelet":
            continue

        for member in relation.members:
            if member.type != "relation" or member.role != "regulatory_element":
                continue

            regulatory_relation = parser.relations.get(member.ref)
            if regulatory_relation is None:
                continue
            if (
                regulatory_relation.tags.get("type") != "regulatory_element"
                or regulatory_relation.tags.get("subtype") != "traffic_light"
            ):
                continue

            output.setdefault(member.ref, set()).add(relation.id)

    return output


def _traffic_light_element(
    regulatory_relation_id: str,
    traffic_light_elements: Mapping[str, list[TrafficLightElement]] | None,
    regulatory_to_lanelet_ids: Mapping[str, set[str]],
) -> list[TrafficLightElement] | None:
    if traffic_light_elements is None:
        return None

    if regulatory_relation_id in traffic_light_elements:
        return traffic_light_elements[regulatory_relation_id]

    lanelet_ids = regulatory_to_lanelet_ids.get(regulatory_relation_id, set())
    for lanelet_id in sorted(lanelet_ids):
        if lanelet_id in traffic_light_elements:
            return traffic_light_elements[lanelet_id]

    return None


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
