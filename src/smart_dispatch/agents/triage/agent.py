"""TriageAgent — wires preprocessing, LLM extraction, location resolution, and dedup."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional
from uuid import uuid4

from smart_dispatch.agents.base import BaseAgent
from smart_dispatch.core.embeddings.base import EmbeddingProvider
from smart_dispatch.core.embeddings.sentence_transformer_provider import SentenceTransformerProvider
from smart_dispatch.core.llm.base import LLMProvider
from smart_dispatch.core.llm.factory import get_default_provider
from smart_dispatch.data.city_graph import CityGraph
from smart_dispatch.data.schemas import MockCall

from .deduplicator import IncidentDeduplicator
from .location_resolver import LocationResolver
from .preprocessor import TranscriptPreprocessor
from .prompts import DEFAULT_PROMPT_VERSION, PROMPT_VERSIONS
from .schemas import LLMTriageExtraction, LocationEntry, TriageResult


class TriageAgent(BaseAgent):
    """Processes raw 112 calls → list of TriageResults (one per resolved location).

    Single-location calls produce a list of one — behaviour is identical to before.
    Multi-location calls (e.g. "fire at IGI and CP") fan out into N independent
    TriageResults, each with its own incident_id and dedup check.
    """

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        embedder: Optional[EmbeddingProvider] = None,
        city_graph: Optional[CityGraph] = None,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
        dedup_threshold: float = 0.75,
        dedup_window_minutes: int = 15,
    ) -> None:
        super().__init__(name="triage")
        self.llm = llm or get_default_provider()
        self.embedder = embedder or SentenceTransformerProvider()
        self.city_graph = city_graph or CityGraph()
        self.preprocessor = TranscriptPreprocessor()
        self.location_resolver = LocationResolver(self.city_graph, self.embedder)
        self.deduplicator = IncidentDeduplicator(
            self.embedder,
            self.city_graph,
            similarity_threshold=dedup_threshold,
            time_window_minutes=dedup_window_minutes,
        )
        self.system_prompt = PROMPT_VERSIONS[prompt_version]
        self._prompt_version = prompt_version

    async def initialize(self) -> None:
        """Preload embedding model and resolver. Call at startup to avoid first-call latency."""
        await self.embedder.load()
        await self.location_resolver.load()
        self.logger.info(
            f"TriageAgent ready | embedder={self.embedder.model_name} "
            f"dim={self.embedder.dimension} | llm={self.llm.provider_name}:{self.llm.model}"
        )

    async def process(self, call: MockCall) -> list[TriageResult]:
        """Main entrypoint: MockCall → list[TriageResult] (one per distinct location).

        For single-location calls the list always has exactly one element, so
        all existing callers that do `results[0]` or iterate work unchanged.
        """
        start = time.perf_counter()
        self._call_count += 1

        # Step 1: preprocess
        clean_transcript = self.preprocessor.clean(call.transcript)

        # Step 2: LLM extraction — now returns a locations list
        extraction: LLMTriageExtraction = await self.llm.structured_output(
            prompt=f"112 call transcript:\n\n{clean_transcript}",
            schema=LLMTriageExtraction,
            system=self.system_prompt,
            temperature=0.1,
            max_tokens=1000,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        results: list[TriageResult] = []

        # Step 3–4: resolve + dedup once per location (fan-out)
        for idx, loc_entry in enumerate(extraction.locations):
            result = await self._process_location(
                call=call,
                extraction=extraction,
                loc_entry=loc_entry,
                location_index=idx,
                elapsed_ms=elapsed_ms,
            )
            results.append(result)

        self.logger.info(
            f"Triaged {call.call_id} → {extraction.incident_type.value}/{extraction.severity.value} "
            f"| locations={len(results)} | {elapsed_ms:.0f}ms"
        )
        return results

    async def _process_location(
        self,
        call: MockCall,
        extraction: LLMTriageExtraction,
        loc_entry: LocationEntry,
        location_index: int,
        elapsed_ms: float,
    ) -> TriageResult:
        """Resolve one location entry and run dedup — returns a single TriageResult."""

        # Step 3: location resolution
        node_id, loc_confidence = await self.location_resolver.resolve(
            raw_text=loc_entry.location_text,
            landmark=loc_entry.location_landmark,
        )

        # Step 4: deduplication (independent per location)
        dup_match = await self.deduplicator.check_duplicate(
            incident_type=extraction.incident_type,
            summary=extraction.summary,
            location_text=loc_entry.location_text,
            node_id=node_id,
            timestamp=call.timestamp,
        )

        if dup_match is not None:
            matched_record, similarity = dup_match
            await self.deduplicator.register_duplicate(
                primary_call_id=matched_record.call_id,
                duplicate_call_id=call.call_id,
            )
            result = TriageResult(
                incident_id=matched_record.incident_id,
                call_id=call.call_id,
                incident_type=extraction.incident_type,
                severity=extraction.severity,
                resources_needed=extraction.resources_needed,
                location_raw=loc_entry.location_text,
                location_landmark=loc_entry.location_landmark,
                location_node_id=node_id,
                location_confidence=loc_confidence,
                location_index=location_index,
                summary=extraction.summary,
                reasoning=extraction.reasoning,
                llm_confidence=extraction.confidence,
                is_duplicate=True,
                duplicate_of_call_id=matched_record.call_id,
                dedup_similarity=similarity,
                processing_time_ms=elapsed_ms,
                llm_provider=self.llm.provider_name,
                llm_model=self.llm.model,
                original_transcript=call.transcript,
            )
        else:
            new_incident_id = f"INC_{uuid4().hex[:8]}"
            await self.deduplicator.add_incident(
                incident_id=new_incident_id,
                call_id=call.call_id,
                incident_type=extraction.incident_type,
                summary=extraction.summary,
                location_text=loc_entry.location_text,
                node_id=node_id,
                timestamp=call.timestamp,
            )
            result = TriageResult(
                incident_id=new_incident_id,
                call_id=call.call_id,
                incident_type=extraction.incident_type,
                severity=extraction.severity,
                resources_needed=extraction.resources_needed,
                location_raw=loc_entry.location_text,
                location_landmark=loc_entry.location_landmark,
                location_node_id=node_id,
                location_confidence=loc_confidence,
                location_index=location_index,
                summary=extraction.summary,
                reasoning=extraction.reasoning,
                llm_confidence=extraction.confidence,
                is_duplicate=False,
                processing_time_ms=elapsed_ms,
                llm_provider=self.llm.provider_name,
                llm_model=self.llm.model,
                original_transcript=call.transcript,
            )

        self.logger.info(
            f"  └─ location[{location_index}] {loc_entry.location_text!r} "
            f"→ {node_id or 'UNRESOLVED'} | dup={result.is_duplicate}"
        )
        return result

    async def health_check(self) -> bool:
        try:
            llm_ok = await self.llm.health_check()
            await self.embedder.load()
            return llm_ok
        except Exception:
            return False

    def stats(self) -> dict:
        return {
            "total_processed": self._call_count,
            "prompt_version": self._prompt_version,
            "llm": f"{self.llm.provider_name}:{self.llm.model}",
            "dedup_stats": self.deduplicator.stats(),
        }
