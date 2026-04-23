"""FastAPI application factory for the Smart Dispatch backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from smart_dispatch.agents.dispatch.agent import DispatchAgent
from smart_dispatch.agents.triage.agent import TriageAgent
from smart_dispatch.api.dependencies import AppState, app_state, get_state
from smart_dispatch.api.routes import calls, decisions, graph, incidents, resources, simulation, stats
from smart_dispatch.api.schemas import StartScenarioRequest
from smart_dispatch.api.simulation import SimulationRunner
from smart_dispatch.api.websocket.routes import router as ws_router
from smart_dispatch.data.resource_db import ResourceDB
from smart_dispatch.data.resource_seeder import seed_resources
from smart_dispatch.orchestration.event_bus import Event, EventBus
from smart_dispatch.orchestration.graph import DispatchOrchestrator

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Smart Dispatch API...")

    # 1. Database
    db = ResourceDB()
    await db.init_db()
    app_state.db = db

    # 2. Agents — TriageAgent pre-loads the embedding model here.
    logger.info("Loading embedding model (may take a moment on first run)...")
    triage = TriageAgent()
    dispatch = DispatchAgent(db=db)
    app_state.triage_agent = triage
    app_state.dispatch_agent = dispatch

    # 3. Seed the resource fleet (idempotent).
    await seed_resources(db)

    # 4. Event bus + orchestrator
    bus = EventBus()
    orchestrator = DispatchOrchestrator(
        triage_agent=triage,
        dispatch_agent=dispatch,
        event_bus=bus,
    )
    app_state.event_bus = bus
    app_state.orchestrator = orchestrator

    # 5. Capture dispatch decisions into memory for the /decisions endpoint.
    async def _capture_decision(event: Event) -> None:
        if event.payload:
            app_state.dispatch_decisions.append(event.payload)

    await bus.subscribe(_capture_decision)

    # 6. Simulation runner
    app_state.simulation = SimulationRunner(orchestrator=orchestrator, event_bus=bus)

    logger.info("Smart Dispatch API ready.")
    yield

    # ---- Shutdown ----
    logger.info("Shutting down...")
    if app_state.simulation and app_state.simulation.is_running:
        await app_state.simulation.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Smart City Dispatch Grid API",
        version="0.1.0",
        description="Phase 6: FastAPI backend + LangGraph orchestration",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Versioned routers (/api/v1/...) ────────────────────────────────────
    app.include_router(calls.router, prefix="/api/v1")
    app.include_router(incidents.router, prefix="/api/v1")
    app.include_router(resources.router, prefix="/api/v1")
    app.include_router(decisions.router, prefix="/api/v1")
    app.include_router(graph.router, prefix="/api/v1")
    app.include_router(stats.router, prefix="/api/v1")
    app.include_router(simulation.router, prefix="/api/v1")

    # ── Short-path aliases (no prefix) ─────────────────────────────────────
    # These mirror the exact paths the demo/smoke-test uses.
    app.include_router(graph.router)          # GET /graph/
    app.include_router(resources.router)      # GET /resources/
    app.include_router(incidents.router)      # GET /incidents/
    app.include_router(decisions.router)      # GET /decisions/
    app.include_router(stats.router)          # GET /stats/

    # WebSocket
    app.include_router(ws_router)

    # ── Inline short-path endpoints that differ in name from the routers ──

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {
            "service": "Smart City Dispatch Grid API",
            "version": "0.1.0",
            "phase": 6,
            "docs": "/docs",
            "health": "/health",
            "endpoints": {
                "graph": "/graph/",
                "resources": "/resources/",
                "incidents": "/incidents/",
                "stats": "/stats/",
                "calls_ingest": "POST /calls/ingest",
                "simulation_reset": "POST /simulation/reset",
                "simulation_start_scenario": "POST /simulation/start-scenario",
                "simulation_start_live": "POST /simulation/start-live",
                "simulation_stop": "POST /simulation/stop",
                "websocket": "/ws/live",
            },
        }

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/calls/ingest", tags=["calls"])
    async def ingest_call(request: Request, state: AppState = Depends(get_state)) -> dict:
        """Short-path alias: ingest a raw transcript through the full pipeline."""
        body = await request.json()
        from smart_dispatch.api.schemas import SingleCallRequest
        from smart_dispatch.api.routes.calls import process_single_call
        req = SingleCallRequest(
            transcript=body.get("transcript", ""),
            call_id=body.get("call_id"),
        )
        result = await process_single_call(req, state)
        return result.model_dump()

    @app.post("/simulation/reset", tags=["simulation"])
    async def sim_reset(state: AppState = Depends(get_state)) -> dict:
        from smart_dispatch.api.routes.simulation import reset_simulation
        return await reset_simulation(state)

    @app.post("/simulation/start-scenario", tags=["simulation"])
    async def sim_start_scenario(body: StartScenarioRequest, state: AppState = Depends(get_state)) -> dict:
        from smart_dispatch.api.routes.simulation import start_scenario
        result = await start_scenario(body, state)
        return result.model_dump()

    @app.post("/simulation/start-live", tags=["simulation"])
    async def sim_start_live(request: Request, state: AppState = Depends(get_state)) -> dict:
        from smart_dispatch.api.schemas import StartLiveRequest
        from smart_dispatch.api.routes.simulation import start_live
        body = await request.json()
        req = StartLiveRequest(**body)
        result = await start_live(req, state)
        return result.model_dump()

    @app.post("/simulation/stop", tags=["simulation"])
    async def sim_stop(state: AppState = Depends(get_state)) -> dict:
        from smart_dispatch.api.routes.simulation import stop_simulation
        result = await stop_simulation(state)
        return result.model_dump()

    @app.get("/simulation/status", tags=["simulation"])
    async def sim_status(state: AppState = Depends(get_state)) -> dict:
        return {"is_running": state.simulation.is_running, "stats": state.simulation.stats()}

    @app.get("/simulation/scenarios", tags=["simulation"])
    async def sim_scenarios() -> dict:
        from smart_dispatch.api.routes.simulation import list_scenarios
        return await list_scenarios()

    return app


app = create_app()
