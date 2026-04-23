"""Agent layer — triage and dispatch agents."""

from smart_dispatch.agents.base import BaseAgent
from smart_dispatch.agents.triage import TriageAgent, TriageResult

__all__ = ["BaseAgent", "TriageAgent", "TriageResult"]
