"""Re-routing decision logic: should a busy vehicle be pulled to a higher-priority incident?"""

from __future__ import annotations

from typing import Optional

from smart_dispatch.data.schemas import Severity
from smart_dispatch.data.resource_db import ResourceDB

from .router import VehicleCandidate
from .schemas import SEVERITY_PRIORITY, ReassignmentEvent


class Rerouter:
    """Decides if an in-flight vehicle should be pulled off its current assignment."""

    MIN_SEVERITY_GAP = 1
    MIN_REMAINING_ETA_SEC = 120

    def __init__(self, db: ResourceDB) -> None:
        self.db = db

    def evaluate_reassignment(
        self,
        candidate: VehicleCandidate,
        new_incident_severity: Severity,
        current_incident_severity: Optional[Severity],
        new_incident_eta_sec: float,
    ) -> tuple[bool, str]:
        """Decide whether to reassign a busy vehicle.

        Returns (should_reassign, reasoning).
        Rules:
        1. Only EN_ROUTE or DISPATCHED vehicles (not ON_SCENE)
        2. New incident must be at least MIN_SEVERITY_GAP more urgent
        3. Don't interrupt if vehicle is < MIN_REMAINING_ETA_SEC from arrival
        """
        if not candidate.is_reroutable:
            return False, "Vehicle already on scene — cannot reassign."

        if current_incident_severity is None:
            return False, "Unknown current incident severity; keeping assignment."

        new_prio = SEVERITY_PRIORITY[new_incident_severity]
        cur_prio = SEVERITY_PRIORITY[current_incident_severity]

        if cur_prio - new_prio < self.MIN_SEVERITY_GAP:
            return False, (
                f"Severity gap insufficient: current {current_incident_severity.value} "
                f"vs new {new_incident_severity.value}."
            )

        if candidate.resource.eta_to_destination_sec is not None:
            if candidate.resource.eta_to_destination_sec < self.MIN_REMAINING_ETA_SEC:
                return False, (
                    f"Vehicle is only {candidate.resource.eta_to_destination_sec:.0f}s "
                    f"from current destination — letting it complete."
                )

        return True, (
            f"Reassigning: new incident is {new_incident_severity.value} "
            f"(vs current {current_incident_severity.value}); "
            f"ETA to new incident {new_incident_eta_sec:.0f}s."
        )
