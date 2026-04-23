"""Vehicle-selection logic: find the best available vehicle for an incident."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from smart_dispatch.data.city_graph import CityGraph
from smart_dispatch.data.resource_db import Resource, ResourceDB, ResourceStatus
from smart_dispatch.data.schemas import ResourceType


@dataclass
class VehicleCandidate:
    """A candidate vehicle being evaluated for dispatch."""

    resource: Resource
    travel_time_sec: float
    path: list[str]
    currently_assigned_to: Optional[str] = None
    current_incident_severity: Optional[str] = None

    @property
    def is_available(self) -> bool:
        return self.resource.status == ResourceStatus.AVAILABLE

    @property
    def is_reroutable(self) -> bool:
        """EN_ROUTE and DISPATCHED vehicles can be re-routed; ON_SCENE cannot."""
        return self.resource.status in (ResourceStatus.DISPATCHED, ResourceStatus.EN_ROUTE)


class VehicleRouter:
    """Selects the best vehicle for a given incident + resource type."""

    def __init__(self, city_graph: CityGraph, db: ResourceDB) -> None:
        self.graph = city_graph
        self.db = db

    async def find_best_available(
        self,
        resource_type: ResourceType,
        destination_node: str,
    ) -> Optional[VehicleCandidate]:
        """Return the AVAILABLE vehicle of the right type with the fastest ETA."""
        candidates = await self._gather_candidates(resource_type, destination_node, include_busy=False)
        if not candidates:
            return None
        return min(candidates, key=lambda c: c.travel_time_sec)

    async def find_all_candidates(
        self,
        resource_type: ResourceType,
        destination_node: str,
        include_busy: bool = True,
    ) -> list[VehicleCandidate]:
        """All candidates sorted by ETA ascending (for re-routing consideration)."""
        candidates = await self._gather_candidates(resource_type, destination_node, include_busy)
        candidates.sort(key=lambda c: c.travel_time_sec)
        return candidates

    async def _gather_candidates(
        self,
        resource_type: ResourceType,
        destination_node: str,
        include_busy: bool,
    ) -> list[VehicleCandidate]:
        if include_busy:
            vehicles: list[Resource] = []
            for s in (ResourceStatus.AVAILABLE, ResourceStatus.DISPATCHED, ResourceStatus.EN_ROUTE):
                vehicles.extend(await self.db.list_resources(status=s, resource_type=resource_type.value))
        else:
            vehicles = await self.db.available_resources_by_type(resource_type.value)

        candidates: list[VehicleCandidate] = []
        for v in vehicles:
            try:
                travel_sec = self.graph.travel_time(v.current_node_id, destination_node)
                path = self.graph.shortest_path(v.current_node_id, destination_node)
                candidates.append(VehicleCandidate(
                    resource=v,
                    travel_time_sec=travel_sec,
                    path=path,
                    currently_assigned_to=v.current_incident_id,
                ))
            except (ValueError, Exception):
                continue
        return candidates
