"""Unit tests for Rerouter.evaluate_reassignment — pure logic, no DB or LLM."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from smart_dispatch.agents.dispatch.rerouter import Rerouter
from smart_dispatch.agents.dispatch.router import VehicleCandidate
from smart_dispatch.data.resource_db import Resource, ResourceStatus
from smart_dispatch.data.schemas import Severity


def _candidate(
    status: ResourceStatus = ResourceStatus.EN_ROUTE,
    eta_remaining: float = 300.0,
    assigned_to: str = "INC_old",
) -> VehicleCandidate:
    resource = MagicMock(spec=Resource)
    resource.id = "AMB_01"
    resource.call_sign = "DELTA-AMB-01"
    resource.status = status
    resource.current_incident_id = assigned_to
    resource.eta_to_destination_sec = eta_remaining
    return VehicleCandidate(
        resource=resource,
        travel_time_sec=180.0,
        path=["N01", "N02"],
        currently_assigned_to=assigned_to,
        current_incident_severity=None,
    )


@pytest.fixture
def rerouter():
    db = MagicMock()
    return Rerouter(db=db)


def test_do_not_reassign_on_scene(rerouter):
    cand = _candidate(status=ResourceStatus.ON_SCENE)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=Severity.LOW,
        new_incident_eta_sec=200.0,
    )
    assert not should
    assert "on scene" in reason.lower() or "cannot" in reason.lower()


def test_do_not_reassign_when_unknown_current_severity(rerouter):
    cand = _candidate(status=ResourceStatus.EN_ROUTE)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=None,
        new_incident_eta_sec=200.0,
    )
    assert not should
    assert "unknown" in reason.lower()


def test_do_not_reassign_insufficient_severity_gap(rerouter):
    cand = _candidate(status=ResourceStatus.EN_ROUTE, eta_remaining=300.0)
    # CRITICAL vs HIGH: gap = 1, but MIN_SEVERITY_GAP = 1 means cur_prio - new_prio must be >= 1
    # CRITICAL=0, HIGH=1 → cur_prio(HIGH)=1, new_prio(CRITICAL)=0 → gap=1, which should pass
    # Let's test CRITICAL vs CRITICAL (gap=0, should not reassign)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=Severity.CRITICAL,
        new_incident_eta_sec=200.0,
    )
    assert not should
    assert "gap" in reason.lower() or "severity" in reason.lower()


def test_do_reassign_when_new_is_critical_and_current_is_medium(rerouter):
    cand = _candidate(status=ResourceStatus.EN_ROUTE, eta_remaining=300.0)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=Severity.MEDIUM,
        new_incident_eta_sec=200.0,
    )
    assert should
    assert "reassigning" in reason.lower() or "critical" in reason.lower()


def test_do_not_reassign_when_vehicle_almost_arrived(rerouter):
    # Vehicle is only 60 seconds from destination (< MIN_REMAINING_ETA_SEC=120)
    cand = _candidate(status=ResourceStatus.EN_ROUTE, eta_remaining=60.0)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=Severity.LOW,
        new_incident_eta_sec=200.0,
    )
    assert not should
    assert "60" in reason or "destination" in reason.lower() or "complete" in reason.lower()


def test_do_reassign_en_route_vehicle_far_from_destination(rerouter):
    cand = _candidate(status=ResourceStatus.EN_ROUTE, eta_remaining=500.0)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=Severity.LOW,
        new_incident_eta_sec=100.0,
    )
    assert should


def test_do_reassign_dispatched_vehicle(rerouter):
    cand = _candidate(status=ResourceStatus.DISPATCHED, eta_remaining=500.0)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=Severity.LOW,
        new_incident_eta_sec=100.0,
    )
    assert should


def test_reason_string_is_informative(rerouter):
    cand = _candidate(status=ResourceStatus.EN_ROUTE, eta_remaining=300.0)
    should, reason = rerouter.evaluate_reassignment(
        candidate=cand,
        new_incident_severity=Severity.CRITICAL,
        current_incident_severity=Severity.MEDIUM,
        new_incident_eta_sec=150.0,
    )
    assert len(reason) > 10
    assert isinstance(reason, str)
