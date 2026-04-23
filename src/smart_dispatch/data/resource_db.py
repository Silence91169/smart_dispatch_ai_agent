"""SQLAlchemy 2.0 async resource database models and session management."""

from __future__ import annotations

import asyncio
import enum as PyEnum
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Float, Integer, String, DateTime, Enum as SAEnum, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from smart_dispatch.config import settings


class ResourceStatus(str, PyEnum.Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    RETURNING = "returning"
    OUT_OF_SERVICE = "out_of_service"


class Base(DeclarativeBase):
    pass


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    call_sign: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    home_node_id: Mapped[str] = mapped_column(String, nullable=False)
    current_node_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ResourceStatus] = mapped_column(
        SAEnum(ResourceStatus), nullable=False, default=ResourceStatus.AVAILABLE
    )
    current_incident_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    eta_to_destination_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_status_change: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_dispatches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Resource {self.call_sign} [{self.status.value}] @ {self.current_node_id}>"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    incident_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    location_node_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location_raw: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    duplicate_call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<Incident {self.id} [{self.status}] {self.incident_type}/{self.severity}>"


class DispatchLog(Base):
    __tablename__ = "dispatch_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[str] = mapped_column(String, nullable=False)
    dispatched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    travel_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    reassigned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<DispatchLog {self.resource_id}→{self.incident_id} {self.travel_time_sec:.0f}s>"


class ResourceNotAvailableError(Exception):
    """Raised when a dispatch is attempted on a non-AVAILABLE resource."""


class ResourceDB:
    """Async database interface for the resource fleet and incidents."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        url = db_url or settings.db_path
        self._engine = create_async_engine(url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )
        self._dispatch_lock = asyncio.Lock()

    async def create_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def init_db(self) -> None:
        """Alias for create_tables — idempotent."""
        await self.create_tables()

    async def reset_db(self) -> None:
        """Drop and recreate all tables (destructive)."""
        await self.drop_tables()
        await self.create_tables()

    def session(self) -> AsyncSession:
        return self._session_factory()

    # -------- Resource methods --------

    async def add_resource(self, resource: Resource) -> None:
        async with self._session_factory() as sess:
            async with sess.begin():
                sess.add(resource)

    async def get_resource(self, resource_id: str) -> Optional[Resource]:
        async with self._session_factory() as sess:
            return await sess.get(Resource, resource_id)

    async def list_resources(
        self, status: Optional[ResourceStatus] = None, resource_type: Optional[str] = None
    ) -> list[Resource]:
        async with self._session_factory() as sess:
            stmt = select(Resource)
            if status is not None:
                stmt = stmt.where(Resource.status == status)
            if resource_type is not None:
                stmt = stmt.where(Resource.resource_type == resource_type)
            result = await sess.execute(stmt)
            return list(result.scalars().all())

    async def available_resources_by_type(self, resource_type: str) -> list[Resource]:
        """Convenience: list AVAILABLE vehicles of a given type."""
        return await self.list_resources(status=ResourceStatus.AVAILABLE, resource_type=resource_type)

    async def dispatch_resource(
        self,
        resource_id: str,
        incident_id: str,
        destination_node: str,
        eta_sec: float,
    ) -> Resource:
        """Atomically mark a resource as dispatched.

        Raises:
            ResourceNotAvailableError: if the resource is not in AVAILABLE status.
            KeyError: if no resource with resource_id exists.
        """
        async with self._dispatch_lock:
            async with self._session_factory() as sess:
                async with sess.begin():
                    resource = await sess.get(Resource, resource_id)
                    if resource is None:
                        raise KeyError(f"Resource '{resource_id}' not found")
                    if resource.status != ResourceStatus.AVAILABLE:
                        raise ResourceNotAvailableError(
                            f"Resource '{resource_id}' is {resource.status.value}, not available"
                        )
                    resource.status = ResourceStatus.DISPATCHED
                    resource.current_incident_id = incident_id
                    resource.current_node_id = destination_node
                    resource.eta_to_destination_sec = eta_sec
                    resource.last_status_change = datetime.now(timezone.utc)
                    resource.total_dispatches += 1
        return resource

    async def update_resource_status(
        self,
        resource_id: str,
        new_status: ResourceStatus,
        current_node: Optional[str] = None,
        new_incident_id: Optional[str] = None,
        eta_sec: Optional[float] = None,
    ) -> Resource:
        """Update a resource's status. Safe for re-routing — does NOT check AVAILABLE guard."""
        async with self._session_factory() as sess:
            async with sess.begin():
                resource = await sess.get(Resource, resource_id)
                if resource is None:
                    raise KeyError(f"Resource '{resource_id}' not found")
                resource.status = new_status
                resource.last_status_change = datetime.now(timezone.utc)
                if current_node is not None:
                    resource.current_node_id = current_node
                if new_incident_id is not None:
                    resource.current_incident_id = new_incident_id
                    resource.total_dispatches += 1
                if eta_sec is not None:
                    resource.eta_to_destination_sec = eta_sec
                if new_status in (ResourceStatus.AVAILABLE, ResourceStatus.RETURNING):
                    resource.current_incident_id = None
                    resource.eta_to_destination_sec = None
        return resource

    # kept for backwards compatibility with existing scripts
    async def update_status(
        self,
        resource_id: str,
        new_status: ResourceStatus,
        incident_id: Optional[str] = None,
    ) -> Resource:
        return await self.update_resource_status(
            resource_id=resource_id,
            new_status=new_status,
            new_incident_id=incident_id,
        )

    # -------- Incident methods --------

    async def create_incident(self, incident: Incident) -> None:
        async with self._session_factory() as sess:
            async with sess.begin():
                sess.add(incident)

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        async with self._session_factory() as sess:
            return await sess.get(Incident, incident_id)

    async def update_incident_status(self, incident_id: str, status: str) -> None:
        async with self._session_factory() as sess:
            async with sess.begin():
                incident = await sess.get(Incident, incident_id)
                if incident is not None:
                    incident.status = status
                    incident.updated_at = datetime.now(timezone.utc)

    async def increment_duplicate_count(self, incident_id: str) -> None:
        async with self._session_factory() as sess:
            async with sess.begin():
                incident = await sess.get(Incident, incident_id)
                if incident is not None:
                    incident.duplicate_call_count += 1
                    incident.updated_at = datetime.now(timezone.utc)

    async def list_incidents(
        self, status: Optional[str] = None, limit: int = 500
    ) -> list[Incident]:
        async with self._session_factory() as sess:
            stmt = select(Incident)
            if status is not None:
                stmt = stmt.where(Incident.status == status)
            stmt = stmt.order_by(Incident.created_at).limit(limit)
            result = await sess.execute(stmt)
            return list(result.scalars().all())

    # -------- Dispatch log methods --------

    async def log_dispatch(self, log: DispatchLog) -> None:
        async with self._session_factory() as sess:
            async with sess.begin():
                sess.add(log)

    async def list_dispatch_logs(
        self, incident_id: Optional[str] = None
    ) -> list[DispatchLog]:
        async with self._session_factory() as sess:
            stmt = select(DispatchLog)
            if incident_id is not None:
                stmt = stmt.where(DispatchLog.incident_id == incident_id)
            stmt = stmt.order_by(DispatchLog.dispatched_at)
            result = await sess.execute(stmt)
            return list(result.scalars().all())

    # -------- Lifecycle --------

    async def close(self) -> None:
        await self._engine.dispose()
