"""Unit tests for VehicleRouter — uses real CityGraph + fresh DB, no LLM."""

import pytest

from smart_dispatch.agents.dispatch.router import VehicleRouter
from smart_dispatch.data.resource_db import ResourceDB, ResourceStatus
from smart_dispatch.data.schemas import ResourceType


@pytest.mark.asyncio
async def test_find_best_available_returns_closest(city_graph, fresh_db):
    router = VehicleRouter(city_graph=city_graph, db=fresh_db)
    candidate = await router.find_best_available(ResourceType.AMBULANCE, "N01")

    assert candidate is not None
    assert candidate.resource.resource_type == "ambulance"
    assert candidate.resource.status == ResourceStatus.AVAILABLE
    assert candidate.travel_time_sec >= 0


@pytest.mark.asyncio
async def test_find_best_available_returns_none_when_type_unavailable(city_graph, fresh_db):
    # Mark all fire trucks as out of service
    fire_trucks = await fresh_db.list_resources(resource_type="fire_truck")
    for ft in fire_trucks:
        await fresh_db.update_resource_status(
            resource_id=ft.id,
            new_status=ResourceStatus.OUT_OF_SERVICE,
            current_node=ft.current_node_id,
            new_incident_id=None,
            eta_sec=None,
        )

    router = VehicleRouter(city_graph=city_graph, db=fresh_db)
    candidate = await router.find_best_available(ResourceType.FIRE_TRUCK, "N01")
    assert candidate is None


@pytest.mark.asyncio
async def test_ignores_wrong_resource_type(city_graph, fresh_db):
    router = VehicleRouter(city_graph=city_graph, db=fresh_db)
    candidate = await router.find_best_available(ResourceType.POLICE_CAR, "N05")

    assert candidate is not None
    assert candidate.resource.resource_type == "police_car"


@pytest.mark.asyncio
async def test_ignores_out_of_service_vehicles(city_graph, fresh_db):
    ambulances = await fresh_db.available_resources_by_type("ambulance")
    assert ambulances, "No ambulances in fleet"

    for amb in ambulances:
        await fresh_db.update_resource_status(
            resource_id=amb.id,
            new_status=ResourceStatus.OUT_OF_SERVICE,
            current_node=amb.current_node_id,
            new_incident_id=None,
            eta_sec=None,
        )

    router = VehicleRouter(city_graph=city_graph, db=fresh_db)
    candidate = await router.find_best_available(ResourceType.AMBULANCE, "N01")
    assert candidate is None


@pytest.mark.asyncio
async def test_picks_lowest_travel_time(city_graph, fresh_db):
    router = VehicleRouter(city_graph=city_graph, db=fresh_db)
    # Ask for ambulance to N01 — should pick the nearest one
    best = await router.find_best_available(ResourceType.AMBULANCE, "N01")
    all_cands = await router.find_all_candidates(ResourceType.AMBULANCE, "N01", include_busy=False)

    assert best is not None
    assert all_cands
    min_eta = min(c.travel_time_sec for c in all_cands)
    assert abs(best.travel_time_sec - min_eta) < 1.0


@pytest.mark.asyncio
async def test_find_all_candidates_includes_busy_when_requested(city_graph, fresh_db):
    # Dispatch one ambulance
    ambulances = await fresh_db.available_resources_by_type("ambulance")
    assert ambulances
    await fresh_db.dispatch_resource(
        resource_id=ambulances[0].id,
        incident_id="INC_test",
        destination_node="N10",
        eta_sec=300.0,
    )

    router = VehicleRouter(city_graph=city_graph, db=fresh_db)
    with_busy = await router.find_all_candidates(
        ResourceType.AMBULANCE, "N01", include_busy=True
    )
    without_busy = await router.find_all_candidates(
        ResourceType.AMBULANCE, "N01", include_busy=False
    )
    assert len(with_busy) > len(without_busy)


@pytest.mark.asyncio
async def test_unreachable_node_does_not_crash(city_graph, fresh_db):
    router = VehicleRouter(city_graph=city_graph, db=fresh_db)
    # "ZZZZ" is not a valid node — should return None gracefully
    candidate = await router.find_best_available(ResourceType.AMBULANCE, "ZZZZ")
    assert candidate is None
