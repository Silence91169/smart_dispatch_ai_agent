"""Edge definitions for the Delhi city road network graph."""

from __future__ import annotations

CITY_EDGES: list[dict] = [
    # Central Delhi connections
    {"from": "N01", "to": "N02", "travel_time_sec": 420, "distance_km": 2.3, "road_type": "arterial"},
    {"from": "N01", "to": "N05", "travel_time_sec": 600, "distance_km": 3.8, "road_type": "arterial"},
    {"from": "N01", "to": "N06", "travel_time_sec": 480, "distance_km": 2.9, "road_type": "arterial"},
    {"from": "N01", "to": "N08", "travel_time_sec": 300, "distance_km": 1.5, "road_type": "arterial"},
    {"from": "N01", "to": "N20", "travel_time_sec": 540, "distance_km": 3.2, "road_type": "arterial"},
    {"from": "N01", "to": "N09", "travel_time_sec": 1200, "distance_km": 8.1, "road_type": "expressway"},
    # South Delhi hospital cluster
    {"from": "N02", "to": "N03", "travel_time_sec": 660, "distance_km": 5.1, "road_type": "arterial"},
    {"from": "N02", "to": "N14", "travel_time_sec": 780, "distance_km": 5.8, "road_type": "arterial"},
    {"from": "N02", "to": "N18", "travel_time_sec": 900, "distance_km": 6.7, "road_type": "arterial"},
    {"from": "N03", "to": "N04", "travel_time_sec": 180, "distance_km": 0.5, "road_type": "local"},
    {"from": "N03", "to": "N14", "travel_time_sec": 540, "distance_km": 3.5, "road_type": "arterial"},
    {"from": "N03", "to": "N16", "travel_time_sec": 480, "distance_km": 2.9, "road_type": "arterial"},
    {"from": "N04", "to": "N13", "travel_time_sec": 600, "distance_km": 4.3, "road_type": "arterial"},
    {"from": "N04", "to": "N16", "travel_time_sec": 420, "distance_km": 2.8, "road_type": "arterial"},
    # Old Delhi / North
    {"from": "N06", "to": "N07", "travel_time_sec": 300, "distance_km": 1.4, "road_type": "local"},
    {"from": "N06", "to": "N08", "travel_time_sec": 360, "distance_km": 1.9, "road_type": "arterial"},
    {"from": "N05", "to": "N06", "travel_time_sec": 540, "distance_km": 3.5, "road_type": "arterial"},
    {"from": "N07", "to": "N20", "travel_time_sec": 360, "distance_km": 1.8, "road_type": "local"},
    {"from": "N08", "to": "N20", "travel_time_sec": 420, "distance_km": 2.6, "road_type": "arterial"},
    {"from": "N08", "to": "N05", "travel_time_sec": 660, "distance_km": 4.4, "road_type": "arterial"},
    {"from": "N12", "to": "N20", "travel_time_sec": 720, "distance_km": 5.1, "road_type": "arterial"},
    {"from": "N12", "to": "N08", "travel_time_sec": 900, "distance_km": 6.6, "road_type": "arterial"},
    # Rohini / West Delhi
    {"from": "N05", "to": "N12", "travel_time_sec": 1080, "distance_km": 8.2, "road_type": "arterial"},
    {"from": "N11", "to": "N12", "travel_time_sec": 1320, "distance_km": 10.5, "road_type": "expressway"},
    {"from": "N11", "to": "N05", "travel_time_sec": 1800, "distance_km": 14.0, "road_type": "expressway"},
    {"from": "N11", "to": "N10", "travel_time_sec": 900, "distance_km": 5.9, "road_type": "arterial"},
    # Airport / Dwarka
    {"from": "N10", "to": "N05", "travel_time_sec": 1500, "distance_km": 19.5, "road_type": "expressway"},
    # South Delhi commercial strip
    {"from": "N13", "to": "N14", "travel_time_sec": 480, "distance_km": 3.6, "road_type": "arterial"},
    {"from": "N13", "to": "N15", "travel_time_sec": 420, "distance_km": 3.0, "road_type": "arterial"},
    {"from": "N13", "to": "N16", "travel_time_sec": 360, "distance_km": 2.4, "road_type": "arterial"},
    {"from": "N13", "to": "N17", "travel_time_sec": 600, "distance_km": 4.2, "road_type": "arterial"},
    {"from": "N14", "to": "N15", "travel_time_sec": 300, "distance_km": 1.8, "road_type": "arterial"},
    {"from": "N15", "to": "N17", "travel_time_sec": 240, "distance_km": 1.3, "road_type": "local"},
    {"from": "N15", "to": "N09", "travel_time_sec": 720, "distance_km": 4.8, "road_type": "arterial"},
    {"from": "N16", "to": "N17", "travel_time_sec": 480, "distance_km": 3.2, "road_type": "arterial"},
    # East Delhi / Yamuna
    {"from": "N17", "to": "N18", "travel_time_sec": 600, "distance_km": 4.5, "road_type": "arterial"},
    {"from": "N18", "to": "N19", "travel_time_sec": 360, "distance_km": 2.2, "road_type": "arterial"},
    {"from": "N19", "to": "N09", "travel_time_sec": 540, "distance_km": 3.4, "road_type": "arterial"},
    {"from": "N09", "to": "N14", "travel_time_sec": 660, "distance_km": 4.6, "road_type": "arterial"},
    {"from": "N09", "to": "N17", "travel_time_sec": 780, "distance_km": 5.5, "road_type": "arterial"},
]
