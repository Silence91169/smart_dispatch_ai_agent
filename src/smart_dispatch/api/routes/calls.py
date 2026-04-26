"""POST /calls/single — process a single transcript through the pipeline."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from smart_dispatch.api.dependencies import AppState, get_state
from smart_dispatch.api.schemas import CallResultResponse, SingleCallRequest
from smart_dispatch.data.schemas import MockCall
from smart_dispatch.orchestration.event_bus import Event, EventType

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/single", response_model=CallResultResponse)
async def process_single_call(
    body: SingleCallRequest,
    state: AppState = Depends(get_state),
) -> CallResultResponse:
    call_id = body.call_id or str(uuid.uuid4())
    call = MockCall(
        call_id=call_id,
        transcript=body.transcript,
        timestamp=datetime.utcnow(),
        scenario_tag="manual",
    )
    # Publish call_received so the frontend feed picks up manual calls too
    if state.event_bus:
        await state.event_bus.publish(Event(
            type=EventType.CALL_RECEIVED,
            call_id=call_id,
            payload={"transcript": body.transcript, "scenario_tag": "manual"},
        ))
    try:
        result = await state.orchestrator.run(call)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    triage_results = result.get("triage_results", [])
    dispatch_decisions = result.get("dispatch_decisions", [])

    return CallResultResponse(
        call_id=call_id,
        triage_results=[t.model_dump(mode="json") for t in triage_results],
        dispatch_decisions=[
            d.model_dump(mode="json") if d is not None else None
            for d in dispatch_decisions
        ],
        skipped=result.get("dispatch_skipped", False),
        skip_reason=result.get("dispatch_skip_reason"),
        latency_ms=result.get("total_latency_ms"),
    )
