"""Seeds the initial 16-vehicle fleet into the resource database."""

from __future__ import annotations

from datetime import datetime, timezone

from smart_dispatch.data.resource_db import Resource, ResourceDB, ResourceStatus

INITIAL_FLEET: list[dict] = [
    # Ambulances — clustered at hospitals and key nodes
    {"id": "AMB_01", "resource_type": "ambulance", "call_sign": "DELTA-AMB-01", "home_node_id": "N03"},
    {"id": "AMB_02", "resource_type": "ambulance", "call_sign": "DELTA-AMB-02", "home_node_id": "N03"},
    {"id": "AMB_03", "resource_type": "ambulance", "call_sign": "DELTA-AMB-03", "home_node_id": "N04"},
    {"id": "AMB_04", "resource_type": "ambulance", "call_sign": "DELTA-AMB-04", "home_node_id": "N04"},
    {"id": "AMB_05", "resource_type": "ambulance", "call_sign": "DELTA-AMB-05", "home_node_id": "N01"},
    {"id": "AMB_06", "resource_type": "ambulance", "call_sign": "DELTA-AMB-06", "home_node_id": "N18"},
    # Fire trucks — distributed across the city
    {"id": "FIRE_01", "resource_type": "fire_truck", "call_sign": "DELTA-FIRE-01", "home_node_id": "N01"},
    {"id": "FIRE_02", "resource_type": "fire_truck", "call_sign": "DELTA-FIRE-02", "home_node_id": "N06"},
    {"id": "FIRE_03", "resource_type": "fire_truck", "call_sign": "DELTA-FIRE-03", "home_node_id": "N13"},
    {"id": "FIRE_04", "resource_type": "fire_truck", "call_sign": "DELTA-FIRE-04", "home_node_id": "N12"},
    # Police cars (PCR) — spread across key zones
    {"id": "PCR_01", "resource_type": "police_car", "call_sign": "DELTA-PCR-01", "home_node_id": "N01"},
    {"id": "PCR_02", "resource_type": "police_car", "call_sign": "DELTA-PCR-02", "home_node_id": "N05"},
    {"id": "PCR_03", "resource_type": "police_car", "call_sign": "DELTA-PCR-03", "home_node_id": "N14"},
    {"id": "PCR_04", "resource_type": "police_car", "call_sign": "DELTA-PCR-04", "home_node_id": "N11"},
    # Hazmat units
    {"id": "HAZ_01", "resource_type": "hazmat_unit", "call_sign": "DELTA-HAZ-01", "home_node_id": "N05"},
    {"id": "HAZ_02", "resource_type": "hazmat_unit", "call_sign": "DELTA-HAZ-02", "home_node_id": "N18"},
]


def _make_resource(spec: dict) -> Resource:
    now = datetime.now(timezone.utc)
    return Resource(
        id=spec["id"],
        resource_type=spec["resource_type"],
        call_sign=spec["call_sign"],
        home_node_id=spec["home_node_id"],
        current_node_id=spec["home_node_id"],
        status=ResourceStatus.AVAILABLE,
        current_incident_id=None,
        eta_to_destination_sec=None,
        last_status_change=now,
        total_dispatches=0,
    )


async def seed_fleet(db: ResourceDB) -> list[Resource]:
    """Insert all 16 vehicles. Returns the created Resource objects."""
    resources = [_make_resource(spec) for spec in INITIAL_FLEET]
    for resource in resources:
        await db.add_resource(resource)
    return resources


async def seed_resources(db: ResourceDB, reset: bool = False) -> list[Resource]:
    """Seed fleet — skips vehicles that already exist (idempotent).

    Args:
        db: ResourceDB instance.
        reset: If True, drops + recreates all tables first.
    """
    if reset:
        await db.reset_db()

    seeded: list[Resource] = []
    for spec in INITIAL_FLEET:
        existing = await db.get_resource(spec["id"])
        if existing is None:
            r = _make_resource(spec)
            await db.add_resource(r)
            seeded.append(r)
    return seeded
