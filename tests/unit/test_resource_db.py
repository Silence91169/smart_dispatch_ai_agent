"""Unit tests for ResourceDB — CRUD, dispatch atomicity."""

import asyncio
import pytest

from smart_dispatch.data.resource_db import ResourceDB, ResourceStatus


@pytest.mark.asyncio
async def test_seed_creates_16_resources(fresh_db):
    resources = await fresh_db.list_resources()
    assert len(resources) == 16


@pytest.mark.asyncio
async def test_available_resources_by_type_ambulance(fresh_db):
    ambs = await fresh_db.available_resources_by_type("ambulance")
    assert len(ambs) == 6
    for a in ambs:
        assert a.status == ResourceStatus.AVAILABLE


@pytest.mark.asyncio
async def test_dispatch_resource_changes_status(fresh_db):
    ambs = await fresh_db.available_resources_by_type("ambulance")
    assert ambs
    r = ambs[0]

    dispatched = await fresh_db.dispatch_resource(
        resource_id=r.id,
        incident_id="INC_test",
        destination_node="N10",
        eta_sec=120.0,
    )

    assert dispatched.status == ResourceStatus.DISPATCHED
    assert dispatched.current_incident_id == "INC_test"
    assert dispatched.total_dispatches == r.total_dispatches + 1


@pytest.mark.asyncio
async def test_dispatch_resource_raises_when_not_available(fresh_db):
    from smart_dispatch.data.resource_db import ResourceNotAvailableError

    ambs = await fresh_db.available_resources_by_type("ambulance")
    r = ambs[0]
    await fresh_db.dispatch_resource(r.id, "INC_1", "N10", 120.0)

    with pytest.raises(ResourceNotAvailableError):
        await fresh_db.dispatch_resource(r.id, "INC_2", "N10", 120.0)


@pytest.mark.asyncio
async def test_dispatch_is_atomic(fresh_db):
    """Two concurrent dispatches on the same resource — exactly one must succeed."""
    ambs = await fresh_db.available_resources_by_type("ambulance")
    assert ambs, "fleet seeder broken?"
    resource_id = ambs[0].id

    async def try_dispatch(incident_id: str) -> bool:
        try:
            await fresh_db.dispatch_resource(resource_id, incident_id, "N01", 120.0)
            return True
        except Exception:
            return False

    results = await asyncio.gather(
        try_dispatch("INC_A"),
        try_dispatch("INC_B"),
    )
    assert sum(results) == 1, f"Expected exactly 1 success, got {sum(results)}"


@pytest.mark.asyncio
async def test_create_and_get_incident(fresh_db):
    from datetime import datetime, timezone
    from smart_dispatch.data.resource_db import Incident

    inc = Incident(
        id="INC_test_001",
        incident_type="fire",
        severity="critical",
        location_node_id="N01",
        location_raw="Connaught Place",
        status="pending",
        duplicate_call_count=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await fresh_db.create_incident(inc)

    fetched = await fresh_db.get_incident("INC_test_001")
    assert fetched is not None
    assert fetched.severity == "critical"
    assert fetched.location_raw == "Connaught Place"


@pytest.mark.asyncio
async def test_update_incident_status(fresh_db):
    from datetime import datetime, timezone
    from smart_dispatch.data.resource_db import Incident

    inc = Incident(
        id="INC_update_test",
        incident_type="medical",
        severity="high",
        location_node_id="N03",
        location_raw="AIIMS",
        status="pending",
        duplicate_call_count=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    await fresh_db.create_incident(inc)
    await fresh_db.update_incident_status("INC_update_test", "dispatched")

    fetched = await fresh_db.get_incident("INC_update_test")
    assert fetched.status == "dispatched"


@pytest.mark.asyncio
async def test_list_resources_by_type(fresh_db):
    fire = await fresh_db.list_resources(resource_type="fire_truck")
    assert len(fire) == 4


@pytest.mark.asyncio
async def test_update_resource_status(fresh_db):
    ambs = await fresh_db.available_resources_by_type("ambulance")
    r = ambs[0]
    await fresh_db.update_resource_status(
        resource_id=r.id,
        new_status=ResourceStatus.ON_SCENE,
        current_node="N05",
        new_incident_id="INC_xyz",
        eta_sec=0.0,
    )
    updated = await fresh_db.get_resource(r.id)
    assert updated.status == ResourceStatus.ON_SCENE
    assert updated.current_node_id == "N05"
