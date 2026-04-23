"""Abstract base class for all agents in the system."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Thin abstract base — keeps all agents structurally consistent."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        self._call_count = 0

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Main entrypoint — each agent defines its own input/output types."""
        ...

    async def health_check(self) -> bool:
        """Override to verify agent dependencies are reachable."""
        return True

    @property
    def call_count(self) -> int:
        return self._call_count
