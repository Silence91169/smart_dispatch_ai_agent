"""Fixed city location fixtures shared by the data generator and the Phase 3 city graph."""

import random
from typing import Optional

CITY_LOCATIONS: list[dict] = [
    {
        "node_id": "N01",
        "name": "4th St & Main Ave",
        "aliases": ["4th and main", "main and 4th", "fourth and main", "main ave and 4th"],
        "lat": 40.7128,
        "lng": -74.0060,
    },
    {
        "node_id": "N02",
        "name": "Central Park Entrance",
        "aliases": ["central park", "the park entrance", "central park gate"],
        "lat": 40.7200,
        "lng": -74.0050,
    },
    {
        "node_id": "N03",
        "name": "Riverside Hospital",
        "aliases": ["riverside hospital", "riverside med center", "the hospital on riverside"],
        "lat": 40.7080,
        "lng": -74.0120,
    },
    {
        "node_id": "N04",
        "name": "Union Station",
        "aliases": ["union station", "the train station", "union depot"],
        "lat": 40.7150,
        "lng": -74.0200,
    },
    {
        "node_id": "N05",
        "name": "City Hall Plaza",
        "aliases": ["city hall", "city hall plaza", "the plaza by city hall"],
        "lat": 40.7165,
        "lng": -74.0150,
    },
    {
        "node_id": "N06",
        "name": "Westside Mall",
        "aliases": ["westside mall", "the mall", "west side shopping center"],
        "lat": 40.7100,
        "lng": -74.0250,
    },
    {
        "node_id": "N07",
        "name": "Memorial Bridge",
        "aliases": ["memorial bridge", "the big bridge", "memorial overpass"],
        "lat": 40.7090,
        "lng": -74.0080,
    },
    {
        "node_id": "N08",
        "name": "5th Ave & Broadway",
        "aliases": ["5th and broadway", "fifth and broadway", "broadway and 5th avenue"],
        "lat": 40.7190,
        "lng": -74.0100,
    },
    {
        "node_id": "N09",
        "name": "Lincoln Elementary School",
        "aliases": ["lincoln school", "lincoln elementary", "the elementary school on lincoln"],
        "lat": 40.7220,
        "lng": -74.0180,
    },
    {
        "node_id": "N10",
        "name": "Oak Street Apartments",
        "aliases": ["oak street apartments", "oak street complex", "the apartments on oak"],
        "lat": 40.7135,
        "lng": -74.0300,
    },
    {
        "node_id": "N11",
        "name": "Maple Ave & 3rd St",
        "aliases": ["maple and 3rd", "maple ave and third", "3rd and maple"],
        "lat": 40.7070,
        "lng": -74.0170,
    },
    {
        "node_id": "N12",
        "name": "Downtown Parking Garage",
        "aliases": ["downtown parking garage", "the parking structure downtown", "5th ave garage"],
        "lat": 40.7145,
        "lng": -74.0130,
    },
    {
        "node_id": "N13",
        "name": "Highway 9 Mile Marker 12",
        "aliases": ["highway 9", "hwy 9 near mile marker 12", "highway 9 at mile 12", "the highway"],
        "lat": 40.7050,
        "lng": -74.0350,
    },
    {
        "node_id": "N14",
        "name": "Riverside Park",
        "aliases": ["riverside park", "the park by the river", "riverside recreation area"],
        "lat": 40.7230,
        "lng": -74.0070,
    },
    {
        "node_id": "N15",
        "name": "Eastside Community Center",
        "aliases": ["community center", "eastside community center", "the eastside center"],
        "lat": 40.7110,
        "lng": -73.9990,
    },
    {
        "node_id": "N16",
        "name": "Harbor View Apartments",
        "aliases": ["harbor view apartments", "harbor view complex", "harberview apts"],
        "lat": 40.7060,
        "lng": -74.0020,
    },
    {
        "node_id": "N17",
        "name": "Gas Station at 7th & Elm",
        "aliases": ["7th and elm", "the gas station on 7th", "elm and 7th street"],
        "lat": 40.7170,
        "lng": -74.0040,
    },
    {
        "node_id": "N18",
        "name": "Jefferson High School",
        "aliases": ["jefferson high", "jefferson high school", "jefferson school"],
        "lat": 40.7240,
        "lng": -74.0220,
    },
    {
        "node_id": "N19",
        "name": "Old Town Square",
        "aliases": ["old town square", "old town", "the old town area"],
        "lat": 40.7155,
        "lng": -74.0090,
    },
    {
        "node_id": "N20",
        "name": "Industrial District",
        "aliases": ["industrial district", "the industrial area", "factory district"],
        "lat": 40.7040,
        "lng": -74.0400,
    },
]

_by_node_id: dict[str, dict] = {loc["node_id"]: loc for loc in CITY_LOCATIONS}


def get_location_by_node_id(node_id: str) -> Optional[dict]:
    """Return the location dict for a given node ID, or None if not found."""
    return _by_node_id.get(node_id)


def get_random_location(rng: random.Random) -> dict:
    """Return a random location. Accepts a Random instance for reproducibility."""
    return rng.choice(CITY_LOCATIONS)


def all_node_ids() -> list[str]:
    """Return all node IDs in fixture order."""
    return [loc["node_id"] for loc in CITY_LOCATIONS]
