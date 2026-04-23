"""Fixed Delhi city location fixtures — shared by the call generator and the Phase 3 city graph."""

from __future__ import annotations

import random
from typing import Optional

CITY_LOCATIONS: list[dict] = [
    {
        "node_id": "N01",
        "name": "Connaught Place",
        "aliases": ["cp", "connaught place", "rajiv chowk", "c p", "connaught", "cp area"],
        "lat": 28.6315,
        "lng": 77.2167,
        "landmark_type": "commercial",
    },
    {
        "node_id": "N02",
        "name": "India Gate",
        "aliases": ["india gate", "india gate circle", "rajpath", "kartavya path", "india gate lawns"],
        "lat": 28.6129,
        "lng": 77.2295,
        "landmark_type": "heritage",
    },
    {
        "node_id": "N03",
        "name": "AIIMS Hospital",
        "aliases": ["aiims", "aiims hospital", "all india institute", "aims hospital", "aiims delhi"],
        "lat": 28.5672,
        "lng": 77.2100,
        "landmark_type": "hospital",
    },
    {
        "node_id": "N04",
        "name": "Safdarjung Hospital",
        "aliases": ["safdarjung", "safdarjung hospital", "safdarjung dispensary", "safdar jung hospital"],
        "lat": 28.5687,
        "lng": 77.2060,
        "landmark_type": "hospital",
    },
    {
        "node_id": "N05",
        "name": "Karol Bagh Market",
        "aliases": ["karol bagh", "karolbagh", "karol bagh market", "kb market", "karol bagh metro"],
        "lat": 28.6519,
        "lng": 77.1909,
        "landmark_type": "market",
    },
    {
        "node_id": "N06",
        "name": "Chandni Chowk",
        "aliases": ["chandni chowk", "chandi chowk", "old delhi market", "chandni chowk metro", "lal kuan"],
        "lat": 28.6506,
        "lng": 77.2303,
        "landmark_type": "market",
    },
    {
        "node_id": "N07",
        "name": "Red Fort",
        "aliases": ["red fort", "lal qila", "lal kila", "red fort metro", "netaji subhash park side"],
        "lat": 28.6562,
        "lng": 77.2410,
        "landmark_type": "heritage",
    },
    {
        "node_id": "N08",
        "name": "New Delhi Railway Station",
        "aliases": ["new delhi station", "ndls", "railway station", "new delhi rly", "paharganj station"],
        "lat": 28.6425,
        "lng": 77.2188,
        "landmark_type": "transport_hub",
    },
    {
        "node_id": "N09",
        "name": "Hazrat Nizamuddin",
        "aliases": ["nizamuddin", "hazrat nizamuddin", "nizamuddin station", "nzm station", "nizamuddin dargah side"],
        "lat": 28.5885,
        "lng": 77.2510,
        "landmark_type": "transport_hub",
    },
    {
        "node_id": "N10",
        "name": "IGI Airport Terminal 3",
        "aliases": ["igi airport", "delhi airport", "terminal 3", "t3", "airport", "indira gandhi airport"],
        "lat": 28.5562,
        "lng": 77.1000,
        "landmark_type": "transport_hub",
    },
    {
        "node_id": "N11",
        "name": "Dwarka Sector 21",
        "aliases": ["dwarka", "dwarka sector 21", "dwarka metro", "dwarka sec 21", "dwarka end"],
        "lat": 28.5522,
        "lng": 77.0586,
        "landmark_type": "residential",
    },
    {
        "node_id": "N12",
        "name": "Rohini Sector 7",
        "aliases": ["rohini", "rohini sector 7", "rohini west", "rithala side", "rohini metro"],
        "lat": 28.7389,
        "lng": 77.0731,
        "landmark_type": "residential",
    },
    {
        "node_id": "N13",
        "name": "Saket Select Citywalk",
        "aliases": ["saket", "saket mall", "select citywalk", "saket select citywalk", "saket metro"],
        "lat": 28.5285,
        "lng": 77.2196,
        "landmark_type": "commercial",
    },
    {
        "node_id": "N14",
        "name": "Lajpat Nagar Central Market",
        "aliases": ["lajpat nagar", "lajpat", "lajpat nagar market", "lnm", "lajpat central market"],
        "lat": 28.5677,
        "lng": 77.2431,
        "landmark_type": "market",
    },
    {
        "node_id": "N15",
        "name": "Nehru Place",
        "aliases": ["nehru place", "nehru place market", "nehru place metro", "np market", "nehru place it hub"],
        "lat": 28.5494,
        "lng": 77.2519,
        "landmark_type": "commercial",
    },
    {
        "node_id": "N16",
        "name": "Hauz Khas Village",
        "aliases": ["hauz khas", "hauz khas village", "hkv", "hauz khas metro", "deer park side"],
        "lat": 28.5533,
        "lng": 77.1951,
        "landmark_type": "commercial",
    },
    {
        "node_id": "N17",
        "name": "Lotus Temple",
        "aliases": ["lotus temple", "bahai temple", "lotus temple metro", "bahai house of worship", "kalkaji mandir side"],
        "lat": 28.5535,
        "lng": 77.2588,
        "landmark_type": "heritage",
    },
    {
        "node_id": "N18",
        "name": "Akshardham Temple",
        "aliases": ["akshardham", "akshardham temple", "swaminarayan akshardham", "akshardham metro", "akshardham delhi"],
        "lat": 28.6127,
        "lng": 77.2773,
        "landmark_type": "heritage",
    },
    {
        "node_id": "N19",
        "name": "Yamuna Bank Metro Station",
        "aliases": ["yamuna bank", "yamuna bank metro", "yamuna bank station", "yamuna crossing", "yamuna bridge metro"],
        "lat": 28.6227,
        "lng": 77.2830,
        "landmark_type": "transport_hub",
    },
    {
        "node_id": "N20",
        "name": "Kashmere Gate ISBT",
        "aliases": ["kashmere gate", "kashmiri gate", "isbt kashmere gate", "inter state bus terminal", "kashmere gate metro"],
        "lat": 28.6675,
        "lng": 77.2280,
        "landmark_type": "transport_hub",
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
