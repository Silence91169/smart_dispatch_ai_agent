"""Unit tests for IncidentPriorityQueue — invariants, ordering, invalidation."""

import pytest
from datetime import datetime, timedelta

from smart_dispatch.agents.dispatch.priority_queue import IncidentPriorityQueue
from smart_dispatch.agents.triage.schemas import TriageResult
from smart_dispatch.data.schemas import IncidentType, ResourceType, Severity


def _triage(
    incident_id: str,
    severity: Severity,
    call_id: str | None = None,
    offset_sec: int = 0,
) -> TriageResult:
    return TriageResult(
        incident_id=incident_id,
        call_id=call_id or f"call_{incident_id}",
        incident_type=IncidentType.FIRE,
        severity=severity,
        resources_needed=[ResourceType.FIRE_TRUCK],
        location_raw="Test location",
        location_node_id="N01",
        summary="test",
        reasoning="test",
        llm_confidence=0.9,
        triaged_at=datetime.utcnow() + timedelta(seconds=offset_sec),
    )


@pytest.mark.asyncio
async def test_critical_pops_before_high_even_when_high_arrived_first():
    q = IncidentPriorityQueue()
    high = _triage("high_1", Severity.HIGH, offset_sec=0)
    critical = _triage("crit_1", Severity.CRITICAL, offset_sec=1)
    await q.push(high)
    await q.push(critical)

    first = await q.pop()
    assert first is not None
    assert first.severity == Severity.CRITICAL


@pytest.mark.asyncio
async def test_two_criticals_pop_in_fifo_order():
    q = IncidentPriorityQueue()
    c1 = _triage("crit_1", Severity.CRITICAL, offset_sec=0)
    c2 = _triage("crit_2", Severity.CRITICAL, offset_sec=1)
    await q.push(c1)
    await q.push(c2)

    first = await q.pop()
    second = await q.pop()
    assert first.incident_id == "crit_1"
    assert second.incident_id == "crit_2"


@pytest.mark.asyncio
async def test_push_same_incident_replaces_old_entry():
    q = IncidentPriorityQueue()
    medium = _triage("inc_1", Severity.MEDIUM)
    critical = _triage("inc_1", Severity.CRITICAL)

    await q.push(medium)
    await q.push(critical)

    result = await q.pop()
    assert result is not None
    assert result.severity == Severity.CRITICAL
    assert await q.pop() is None  # only one effective entry


@pytest.mark.asyncio
async def test_peek_does_not_remove():
    q = IncidentPriorityQueue()
    await q.push(_triage("inc_1", Severity.HIGH))

    peeked = await q.peek()
    assert peeked is not None
    assert peeked.incident_id == "inc_1"
    assert await q.size() == 1

    popped = await q.pop()
    assert popped is not None
    assert popped.incident_id == "inc_1"


@pytest.mark.asyncio
async def test_size_excludes_invalidated():
    q = IncidentPriorityQueue()
    await q.push(_triage("inc_1", Severity.HIGH))
    await q.push(_triage("inc_2", Severity.HIGH))
    await q.remove("inc_1")

    assert await q.size() == 1


@pytest.mark.asyncio
async def test_remove_marks_entry_invalidated():
    q = IncidentPriorityQueue()
    await q.push(_triage("inc_1", Severity.MEDIUM))
    removed = await q.remove("inc_1")
    assert removed is True

    result = await q.pop()
    assert result is None  # invalidated entry skipped


@pytest.mark.asyncio
async def test_remove_nonexistent_returns_false():
    q = IncidentPriorityQueue()
    assert await q.remove("does_not_exist") is False


@pytest.mark.asyncio
async def test_snapshot_returns_in_priority_order():
    q = IncidentPriorityQueue()
    await q.push(_triage("low", Severity.LOW))
    await q.push(_triage("critical", Severity.CRITICAL))
    await q.push(_triage("medium", Severity.MEDIUM))
    await q.push(_triage("high", Severity.HIGH))

    snap = await q.snapshot()
    severities = [t.severity for t in snap]
    assert severities == [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]


@pytest.mark.asyncio
async def test_pop_empty_returns_none():
    q = IncidentPriorityQueue()
    assert await q.pop() is None


@pytest.mark.asyncio
async def test_severity_ordering_all_levels():
    q = IncidentPriorityQueue()
    for sev in [Severity.LOW, Severity.HIGH, Severity.MEDIUM, Severity.CRITICAL]:
        await q.push(_triage(f"inc_{sev.value}", sev))

    order = []
    while True:
        item = await q.pop()
        if item is None:
            break
        order.append(item.severity)

    assert order == [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
