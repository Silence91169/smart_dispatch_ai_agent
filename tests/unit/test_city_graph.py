"""Sanity tests for CityGraph — connectivity, routing, node/edge counts."""

import pytest

from smart_dispatch.data.city_graph import CityGraph


def test_graph_has_expected_node_count(city_graph):
    assert len(city_graph.graph.nodes) == 20


def test_graph_has_edges(city_graph):
    assert len(city_graph.graph.edges) > 0


def test_graph_is_connected(city_graph):
    assert city_graph.validate_connectivity()


def test_shortest_path_same_node(city_graph):
    path = city_graph.shortest_path("N01", "N01")
    assert path == ["N01"]


def test_shortest_path_returns_valid_sequence(city_graph):
    path = city_graph.shortest_path("N01", "N10")
    assert path[0] == "N01"
    assert path[-1] == "N10"
    # Verify consecutive nodes are adjacent
    for a, b in zip(path, path[1:]):
        assert city_graph.graph.has_edge(a, b), f"No edge between {a} and {b}"


def test_travel_time_positive(city_graph):
    t = city_graph.travel_time("N01", "N10")
    assert t > 0


def test_travel_time_same_node_is_zero(city_graph):
    t = city_graph.travel_time("N01", "N01")
    assert t == 0.0


def test_stats_returns_dict_with_expected_keys(city_graph):
    stats = city_graph.stats()
    assert "nodes" in stats
    assert "edges" in stats
    assert stats["nodes"] == 20


def test_all_nodes_reachable_from_n01(city_graph):
    import networkx as nx
    reachable = nx.descendants(city_graph.graph, "N01") | {"N01"}
    assert len(reachable) == 20
