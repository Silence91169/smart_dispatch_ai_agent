"""Shared test fixtures for the smart-dispatch test suite."""

import asyncio
import pytest
import pytest_asyncio
from pathlib import Path

from smart_dispatch.data.resource_db import ResourceDB
from smart_dispatch.data.city_graph import CityGraph
from smart_dispatch.data.resource_seeder import seed_resources
from smart_dispatch.data.golden_dataset import load_golden_dataset
from tests.mocks.mock_llm import MockLLMProvider


@pytest.fixture(scope="session")
def city_graph():
    return CityGraph()


@pytest.fixture(scope="session")
def golden_cases():
    return load_golden_dataset()


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest_asyncio.fixture
async def fresh_db(tmp_path):
    """A clean ResourceDB per test, backed by a temp SQLite file."""
    db_path = tmp_path / "test.db"
    db = ResourceDB(db_url=f"sqlite+aiosqlite:///{db_path}")
    await db.init_db()
    await seed_resources(db, reset=True)
    yield db
    await db.close()
