"""POST /simulation/* — control the background simulation runner."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.schemas import (
    SimulationStatusResponse,
    StartLiveRequest,
    StartScenarioRequest,
)
from smart_dispatch.data.call_generator import MockCallGenerator
from smart_dispatch.data.resource_seeder import seed_resources

router = APIRouter(prefix="/simulation", tags=["simulation"])

_SCENARIOS_PATH = Path(__file__).parents[4] / "tests" / "fixtures" / "incident_scenarios.json"


def _load_scenarios() -> dict:
    if not _SCENARIOS_PATH.exists():
        return {"scenarios": []}
    with _SCENARIOS_PATH.open() as f:
        return json.load(f)


@router.get("/scenarios")
async def list_scenarios() -> dict:
    data = _load_scenarios()
    return {"scenarios": [s["name"] for s in data.get("scenarios", [])]}


@router.get("/status", response_model=SimulationStatusResponse)
async def simulation_status(state: AppState = Depends(get_state)) -> SimulationStatusResponse:
    return SimulationStatusResponse(
        is_running=state.simulation.is_running,
        stats=state.simulation.stats(),
    )


@router.post("/start/scenario", response_model=SimulationStatusResponse)
async def start_scenario(
    body: StartScenarioRequest,
    state: AppState = Depends(get_state),
) -> SimulationStatusResponse:
    data = _load_scenarios()
    scenario = next(
        (s for s in data.get("scenarios", []) if s["name"] == body.scenario_name), None
    )
    if scenario is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{body.scenario_name}' not found. "
                   f"Available: {[s['name'] for s in data.get('scenarios', [])]}",
        )

    gen = MockCallGenerator(seed=scenario.get("seed"))
    calls = gen.generate_batch(
        total_calls=scenario["total_calls"],
        duplicate_ratio=scenario.get("duplicate_ratio", 0.3),
        template_mix=scenario.get("template_mix"),
        time_window_minutes=scenario.get("time_window_minutes", 10.0),
    )

    await state.simulation.start_scenario(
        scenario_name=body.scenario_name,
        calls=calls,
        speed_multiplier=body.speed_multiplier,
    )
    return SimulationStatusResponse(
        is_running=state.simulation.is_running,
        stats=state.simulation.stats(),
    )


@router.post("/start/live", response_model=SimulationStatusResponse)
async def start_live(
    body: StartLiveRequest,
    state: AppState = Depends(get_state),
) -> SimulationStatusResponse:
    await state.simulation.start_live(
        calls_per_minute=body.calls_per_minute,
        seed=body.seed,
        max_calls=body.max_calls,
        duplicate_ratio=body.duplicate_ratio,
    )
    return SimulationStatusResponse(
        is_running=state.simulation.is_running,
        stats=state.simulation.stats(),
    )


@router.post("/stop", response_model=SimulationStatusResponse)
async def stop_simulation(state: AppState = Depends(get_state)) -> SimulationStatusResponse:
    await state.simulation.stop()
    return SimulationStatusResponse(
        is_running=state.simulation.is_running,
        stats=state.simulation.stats(),
    )


@router.post("/reset")
async def reset_simulation(state: AppState = Depends(get_state)) -> dict:
    """Stop simulation, wipe DB, re-seed fleet."""
    if state.simulation.is_running:
        await state.simulation.stop()
    await state.db.reset_db()
    await seed_resources(state.db)
    state.dispatch_decisions.clear()
    if state.triage_agent is not None:
        state.triage_agent.deduplicator.reset()
    return {"status": "reset", "message": "DB wiped and fleet re-seeded."}
