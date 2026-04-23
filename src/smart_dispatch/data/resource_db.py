"""SQLAlchemy 2.0 async resource database models and session management."""

from __future__ import annotations

import asyncio
import enum as PyEnum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, Enum as SAEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select

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


class ResourceNotAvailableError(Exception):
    """Raised when a dispatch is attempted on a non-AVAILABLE resource."""


class ResourceDB:
    """Async database interface for the resource fleet."""

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

    def session(self) -> AsyncSession:
        return self._session_factory()

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

    async def update_status(
        self,
        resource_id: str,
        new_status: ResourceStatus,
        incident_id: Optional[str] = None,
    ) -> Resource:
        """Update a resource's status, optionally clearing the incident link."""
        async with self._session_factory() as sess:
            async with sess.begin():
                resource = await sess.get(Resource, resource_id)
                if resource is None:
                    raise KeyError(f"Resource '{resource_id}' not found")
                resource.status = new_status
                resource.last_status_change = datetime.now(timezone.utc)
                if incident_id is not None:
                    resource.current_incident_id = incident_id
                if new_status in (ResourceStatus.AVAILABLE, ResourceStatus.RETURNING):
                    resource.eta_to_destination_sec = None
        return resource

    async def close(self) -> None:
        await self._engine.dispose()
