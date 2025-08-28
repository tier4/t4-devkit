from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Final

from attrs import define, field

from t4_devkit.typing import Vector3

__all__ = ["LaneletParser"]


@define
class Node:
    """Represents an OSM node (point) with coodrinates and attributes."""

    id: str
    lat: float
    lon: float
    local_x: float | None = None
    local_y: float | None = None
    ele: float | None = None
    tags: dict[str, str] = field(factory=dict)


@define
class Way:
    """Represents an OSM way (line/polyline) with node references and attributes."""

    id: str
    node_refs: list[str] = field(factory=list)
    tags: dict[str, str] = field(factory=dict)


@define
class Relation:
    """Represents an OSM relation with member references and attributes."""

    id: str
    members: list[Member] = field(factory=list)
    tags: dict[str, str] = field(factory=dict)


@define
class Member:
    """Represents an OSM relation member."""

    type: str
    ref: str
    role: str


class LaneletParser:
    """Parses an OSM XML file into a dictionary of nodes, ways, and relations."""

    elevation_scale: float = 1.0
    default_elevation: float = 0.0

    def __init__(self, filepath: str, *, verbose: bool = False):
        """Initializes the parser with the given file path.

        Args:
            filepath (str): The path to the OSM XML file to parse.
            verbose (bool, optional): Whether to print basic statistics about the parsed OSM data.
        """

        tree = ET.parse(filepath)
        root = tree.getroot()

        self._nodes = _parse_nodes(root)
        self._ways = _parse_ways(root)
        self._relations = _parse_relations(root)

        if verbose:
            self._print_statistics()

    def _print_statistics(self) -> None:
        """Print basic statistics about the parsed OSM data."""
        num_lines: Final[int] = 50

        print("\n" + "=" * num_lines)
        print("OSM MAP STATISTICS")
        print("=" * num_lines)
        print(f"Nodes: {len(self.nodes)}")
        print(f"Ways: {len(self.ways)}")
        print(f"Relations: {len(self.relations)}")

        # Analyze way types
        way_types = defaultdict(int)
        for way in self.ways.values():
            way_type = way.tags.get("type", "unknown")
            subtype = way.tags.get("subtype", "")
            key = f"{way_type}:{subtype}" if subtype else way_type
            way_types[key] += 1

        print("\nWay Types:")
        for way_type, count in sorted(way_types.items()):
            print(f"  {way_type}: {count}")

        # Analyze relation types
        relation_types = defaultdict(int)
        for relation in self.relations.values():
            rel_type = relation.tags.get("type", "unknown")
            subtype = relation.tags.get("subtype", "")
            key = f"{rel_type}:{subtype}" if subtype else rel_type
            relation_types[key] += 1

        print("\nRelation Types:")
        for rel_type, count in sorted(relation_types.items()):
            print(f"  {rel_type}: {count}")

        # Coordinate system info
        local_coord_nodes = sum(
            1
            for node in self.nodes.values()
            if node.local_x is not None and node.local_y is not None
        )
        print(f"\nNodes with local coordinates: {local_coord_nodes}/{len(self.nodes)}")
        print("=" * num_lines)

    @property
    def nodes(self) -> dict[str, Node]:
        return self._nodes

    @property
    def ways(self) -> dict[str, Way]:
        return self._ways

    @property
    def relations(self) -> dict[str, Relation]:
        return self._relations

    def coordinates(self, node: Node, *, as_geographic: bool = False) -> Vector3:
        """Return coordinates of a node, preferring local coordinates if available.

        Args:
            node (Node): The node to get coordinates for.
            as_geographic (bool): Whether to return coordinates in geographic (lat, lon, elevation) format.

        Returns:
            A Vector3 coordinate for the node.
        """
        if node.local_x is not None and node.local_y is not None and not as_geographic:
            x, y = node.local_x, node.local_y
        else:
            # Convert lat/lon to a simple projection (not accurate for large areas)
            x, y = node.lat, node.lon

        z = node.ele * self.elevation_scale if node.ele is not None else self.default_elevation

        return Vector3(x, y, z)

    def way_coordinates(self, way: Way, *, as_geographic: bool = False) -> list[Vector3]:
        """Return coordinates of a way, preferring local coordinates if available.

        Args:
            way (Way): The way to get coordinates for.
            as_geographic: Whether to return coordinates in geographic (lat, lon, elevation) format.

        Returns:
            A list of Vector3 coordinates for the way.
        """
        return [
            self.coordinates(self.nodes[node_ref], as_geographic=as_geographic)
            for node_ref in way.node_refs
            if node_ref in self.nodes
        ]


def _parse_nodes(root: ET.Element[str]) -> dict[str, Node]:
    output: dict[str, Node] = {}
    for node_elem in root.findall("node"):
        node_id = node_elem.get("id")
        node_lat = float(node_elem.get("lat"))
        node_lon = float(node_elem.get("lon"))

        tags: dict[str, str] = {}
        local_x = None
        local_y = None
        ele = None
        for tag_elem in node_elem.findall("tag"):
            key = tag_elem.get("k")
            value = tag_elem.get("v")
            tags[key] = value

            # extract local coordinates if available
            if key == "local_x":
                local_x = float(value)
            elif key == "local_y":
                local_y = float(value)
            elif key == "ele":
                ele = float(value)

        output[node_id] = Node(
            id=node_id,
            lat=node_lat,
            lon=node_lon,
            tags=tags,
            local_x=local_x,
            local_y=local_y,
            ele=ele,
        )

    return output


def _parse_ways(root: ET.Element[str]) -> dict[str, Way]:
    output: dict[str, Way] = {}
    for way_elem in root.findall("way"):
        way_id = way_elem.get("id")
        node_refs = [nd.get("ref") for nd in way_elem.findall("nd")]

        tags: dict[str, str] = {
            tag_elem.get("k"): tag_elem.get("v") for tag_elem in way_elem.findall("tag")
        }

        output[way_id] = Way(id=way_id, node_refs=node_refs, tags=tags)

    return output


def _parse_relations(root: ET.Element[str]) -> dict[str, Relation]:
    output: dict[str, Relation] = {}
    for relation_elem in root.findall("relation"):
        relation_id = relation_elem.get("id")

        members = [
            Member(
                type=member_elem.get("type"),
                ref=member_elem.get("ref"),
                role=member_elem.get("role", ""),
            )
            for member_elem in relation_elem.findall("member")
        ]

        tags: dict[str, str] = {
            tag_elem.get("k"): tag_elem.get("v") for tag_elem in relation_elem.findall("tag")
        }

        output[relation_id] = Relation(id=relation_id, members=members, tags=tags)

    return output
