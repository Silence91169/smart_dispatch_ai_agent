"""Integration tests for the FastAPI REST endpoints via TestClient.

Uses the real app lifespan (loads embedding model, seeds fleet).
Marked integration because of the startup time.
"""

import os
import pytest
from fastapi.testclient import TestClient

from smart_dispatch.api.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    if not any(os.getenv(k) for k in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")):
        pytest.skip("No LLM API key — set GROQ_API_KEY to run integration tests")
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_root_returns_service_info(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "Smart City Dispatch Grid API"


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_graph_endpoint_returns_nodes_and_edges(client):
    r = client.get("/graph/")
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 20


def test_resources_endpoint_returns_fleet(client):
    r = client.get("/resources/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 16


def test_incidents_endpoint_initially_empty(client):
    r = client.get("/incidents/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_stats_endpoint_returns_expected_keys(client):
    r = client.get("/stats/")
    assert r.status_code == 200
    data = r.json()
    assert "resources_total" in data
    assert data["resources_total"] == 16
    assert "resources_available" in data


def test_simulation_status_endpoint(client):
    r = client.get("/simulation/status")
    assert r.status_code == 200
    data = r.json()
    assert "is_running" in data


def test_simulation_reset_endpoint(client):
    r = client.post("/simulation/reset")
    assert r.status_code == 200


def test_calls_ingest_processes_transcript(client):
    r = client.post(
        "/calls/ingest",
        json={"transcript": "fire at CP, building burning"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "call_id" in data
    assert "triage" in data
