"""Delhi city graph — NetworkX wrapper for travel-time routing."""

from __future__ import annotations

from typing import Optional

import networkx as nx
from geopy.distance import distance as haversine_distance

from smart_dispatch.data.city_fixtures import CITY_LOCATIONS, get_location_by_node_id
from smart_dispatch.data.graph_fixtures import CITY_EDGES


class CityGraph:
    """Undirected weighted graph of Delhi landmarks.

    Edge weight ``travel_time_sec`` is used for all shortest-path calculations.
    """

    def __init__(self) -> None:
        self._g: nx.Graph = nx.Graph()
        self._build()

    def _build(self) -> None:
        for loc in CITY_LOCATIONS:
            self._g.add_node(
                loc["node_id"],
                name=loc["name"],
                lat=loc["lat"],
                lng=loc["lng"],
                landmark_type=loc["landmark_type"],
            )
        for edge in CITY_EDGES:
            self._g.add_edge(
                edge["from"],
                edge["to"],
                travel_time_sec=edge["travel_time_sec"],
                distance_km=edge["distance_km"],
                road_type=edge["road_type"],
            )

    def travel_time(self, from_node: str, to_node: str) -> float:
        """Return shortest travel time in seconds between two node IDs."""
        return nx.shortest_path_length(
            self._g, from_node, to_node, weight="travel_time_sec"
        )

    def shortest_path(self, from_node: str, to_node: str) -> list[str]:
        """Return ordered list of node IDs on the shortest path."""
        return nx.shortest_path(self._g, from_node, to_node, weight="travel_time_sec")

    def nearest_node_to_coords(self, lat: float, lng: float) -> str:
        """Return the node ID closest (haversine) to the given coordinates."""
        best_node: str = ""
        best_dist = float("inf")
        for node_id, data in self._g.nodes(data=True):
            d = haversine_distance((lat, lng), (data["lat"], data["lng"])).km
            if d < best_dist:
                best_dist = d
                best_node = node_id
        return best_node

    def resolve_location(self, raw_text: str) -> Optional[str]:
        """Map free-text location mention to a node ID via alias substring match.

        Returns the first matching node ID, or ``None`` if no alias matches.
        """
        text_lower = raw_text.lower()
        for loc in CITY_LOCATIONS:
            for alias in loc["aliases"]:
                if alias in text_lower:
                    return loc["node_id"]
        return None

    def validate_connectivity(self) -> bool:
        """Return True if the graph is fully connected."""
        return nx.is_connected(self._g)

    def stats(self) -> dict:
        """Return basic graph statistics."""
        return {
            "nodes": self._g.number_of_nodes(),
            "edges": self._g.number_of_edges(),
            "connected": self.validate_connectivity(),
            "avg_degree": round(
                sum(d for _, d in self._g.degree()) / self._g.number_of_nodes(), 2
            ),
        }

    @property
    def graph(self) -> nx.Graph:
        """Direct access to the underlying NetworkX graph."""
        return self._g


_default_graph: Optional[CityGraph] = None


def get_city_graph() -> CityGraph:
    """Return the module-level singleton CityGraph."""
    global _default_graph
    if _default_graph is None:
        _default_graph = CityGraph()
    return _default_graph
