"""Core 112 call generator — deterministic when seeded."""

import random
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from faker import Faker

from smart_dispatch.data.city_fixtures import CITY_LOCATIONS, get_random_location
from smart_dispatch.data.incident_templates import (
    IncidentTemplate,
    all_templates,
    get_template,
)
from smart_dispatch.data.schemas import MockCall

_DEFAULT_TEMPLATE_MIX: dict[str, float] = {
    "cardiac_arrest": 0.15,
    "house_fire_residential": 0.10,
    "apartment_fire_highrise": 0.05,
    "car_accident_injury": 0.15,
    "car_accident_minor": 0.15,
    "armed_robbery": 0.08,
    "assault_in_progress": 0.07,
    "gas_leak": 0.05,
    "downed_power_line": 0.10,
    "person_choking": 0.10,
}

_FILLER_WORDS = ["uhh", "um", "uh", "like", "I mean", "you know"]
_INTERJECTIONS = [
    "oh god", "help me", "please", "oh no", "oh my god",
    "oh shit", "hurry", "listen", "please help",
]
_VOWELS = set("aeiouAEIOU")


class MockCallGenerator:
    """Generate realistic, deterministic 112 call transcripts.

    Args:
        seed: Optional integer seed.  When provided, the same seed produces
            identical output across runs.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)
        self.faker = Faker()
        if seed is not None:
            Faker.seed(seed)
        self._event_counter: int = 0
        self._templates: list[IncidentTemplate] = all_templates()
        self._template_ids: list[str] = [t.template_id for t in self._templates]
        # Maps event_id -> template_id so duplicates use the same incident type
        self._event_template_map: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_call(self, template_id: Optional[str] = None) -> MockCall:
        """Generate a single 112 call.

        Args:
            template_id: If ``None``, one is chosen from the default distribution.

        Returns:
            A :class:`MockCall` with a fresh ``event_id``.
        """
        template = get_template(template_id) if template_id else self.rng.choice(self._templates)
        event_id = f"event_{template.template_id}_{uuid4().hex[:6]}"
        self._event_template_map[event_id] = template.template_id
        return self._render_call(template, event_id)

    def generate_event_cluster(
        self,
        template_id: Optional[str] = None,
        num_calls: int = 3,
    ) -> list[MockCall]:
        """Generate ``num_calls`` calls all describing the same event.

        All share the same ``event_id`` but use different transcript variants,
        different location aliases, and staggered timestamps.

        Args:
            template_id: If ``None``, one is chosen randomly.
            num_calls: Total calls to generate (including the primary).

        Returns:
            List of :class:`MockCall` objects sorted by timestamp.
        """
        template = get_template(template_id) if template_id else self.rng.choice(self._templates)
        event_id = f"event_{template.template_id}_{uuid4().hex[:6]}"
        self._event_template_map[event_id] = template.template_id

        location = get_random_location(self.rng)
        base_time = datetime.utcnow()
        calls: list[MockCall] = []

        for i in range(num_calls):
            offset_secs = sum(
                self.rng.randint(5, 90) for _ in range(i)
            )
            timestamp = base_time + timedelta(seconds=offset_secs)
            call = self._render_call(
                template,
                event_id,
                location=location,
                timestamp=timestamp,
            )
            calls.append(call)

        calls.sort(key=lambda c: c.timestamp)
        return calls

    def generate_batch(
        self,
        total_calls: int,
        duplicate_ratio: float = 0.3,
        template_mix: Optional[dict[str, float]] = None,
        time_window_minutes: float = 10.0,
    ) -> list[MockCall]:
        """Generate a realistic mixed batch of calls.

        Args:
            total_calls: Target number of calls.
            duplicate_ratio: Fraction of calls that are duplicates of an existing event.
            template_mix: Optional weight map ``{template_id: weight}``.  Weights need
                not sum to 1 — they are normalised internally.
            time_window_minutes: Spread timestamps uniformly over this many minutes.

        Returns:
            List of :class:`MockCall` sorted by timestamp.
        """
        mix = template_mix or _DEFAULT_TEMPLATE_MIX
        num_duplicate_calls = int(total_calls * duplicate_ratio)
        num_unique = total_calls - num_duplicate_calls

        base_time = datetime.utcnow()
        window_secs = time_window_minutes * 60.0

        # --- generate unique events ---
        unique_calls: list[MockCall] = []
        for _ in range(num_unique):
            tid = self._weighted_pick(mix)
            call = self.generate_call(tid)
            unique_calls.append(call)

        # --- generate duplicates referencing random unique events ---
        dup_calls: list[MockCall] = []
        remaining = num_duplicate_calls
        while remaining > 0:
            source = self.rng.choice(unique_calls)
            source_tid = self._event_template_map.get(source.event_id or "")
            n_extra = min(self.rng.randint(1, 3), remaining)
            for _ in range(n_extra):
                dup = self._render_duplicate(source, source_tid)
                dup_calls.append(dup)
                remaining -= 1

        # --- assign timestamps spread over the window ---
        all_calls: list[MockCall] = unique_calls + dup_calls
        result: list[MockCall] = []
        for call in all_calls:
            t = base_time + timedelta(seconds=self.rng.uniform(0, window_secs))
            result.append(call.model_copy(update={"timestamp": t}))

        result.sort(key=lambda c: c.timestamp)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _render_call(
        self,
        template: IncidentTemplate,
        event_id: str,
        location: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> MockCall:
        if location is None:
            location = get_random_location(self.rng)

        # 70% chance: use a messy alias instead of canonical name
        if self.rng.random() < 0.70 and location["aliases"]:
            loc_text = self.rng.choice(location["aliases"])
        else:
            loc_text = location["name"]

        variant = self.rng.choice(template.transcript_variants)
        detail = self.rng.choice(template.detail_pool) if template.detail_pool else ""
        panic = self.rng.choice(template.panic_phrases) if template.panic_phrases else ""

        transcript = variant.format(location=loc_text, detail=detail, panic=panic)
        transcript = self._apply_noise(transcript)

        return MockCall(
            transcript=transcript,
            timestamp=timestamp or datetime.utcnow(),
            caller_phone=self.faker.phone_number(),
            event_id=event_id,
        )

    def _render_duplicate(
        self,
        source: MockCall,
        template_id: Optional[str],
    ) -> MockCall:
        """Render a new call about the same event as ``source``."""
        try:
            template = get_template(template_id) if template_id else self.rng.choice(self._templates)
        except KeyError:
            template = self.rng.choice(self._templates)

        location = get_random_location(self.rng)
        # Slightly different alias to simulate callers describing same place differently
        if location["aliases"]:
            loc_text = self.rng.choice(location["aliases"])
        else:
            loc_text = location["name"]

        variant = self.rng.choice(template.transcript_variants)
        detail = self.rng.choice(template.detail_pool) if template.detail_pool else ""
        panic = self.rng.choice(template.panic_phrases) if template.panic_phrases else ""

        transcript = variant.format(location=loc_text, detail=detail, panic=panic)
        transcript = self._apply_noise(transcript)

        return MockCall(
            transcript=transcript,
            timestamp=datetime.utcnow(),
            caller_phone=self.faker.phone_number(),
            event_id=source.event_id,
        )

    def _apply_noise(self, text: str) -> str:
        """Apply realism noise to a transcript."""
        # 20%: all lowercase
        if self.rng.random() < 0.20:
            text = text.lower()

        # 15%: inject 1-2 typos
        if self.rng.random() < 0.15:
            n_typos = self.rng.randint(1, 2)
            for _ in range(n_typos):
                text = self._inject_typo(text)

        # 10%: add filler words
        if self.rng.random() < 0.10:
            words = text.split()
            if len(words) > 3:
                pos = self.rng.randint(1, min(4, len(words) - 1))
                filler = self.rng.choice(_FILLER_WORDS)
                words.insert(pos, filler)
                text = " ".join(words)

        # 25%: prepend an interjection
        if self.rng.random() < 0.25:
            interjection = self.rng.choice(_INTERJECTIONS)
            text = f"{interjection}, {text}"

        # 10%: add trailing ellipsis or incomplete sentence
        if self.rng.random() < 0.10:
            endings = ["...", " please...", ", hurry...", " I don't know what to do..."]
            text = text.rstrip(".!?") + self.rng.choice(endings)

        return text

    def _inject_typo(self, text: str) -> str:
        """Swap two adjacent chars or drop a vowel in a random word."""
        words = text.split()
        candidates = [(i, w) for i, w in enumerate(words) if len(w) > 3 and w.isalpha()]
        if not candidates:
            return text
        idx, word = self.rng.choice(candidates)
        if self.rng.random() < 0.5:
            # Swap adjacent chars
            pos = self.rng.randint(0, len(word) - 2)
            word = word[:pos] + word[pos + 1] + word[pos] + word[pos + 2:]
        else:
            # Drop an interior vowel
            vowel_positions = [i for i, c in enumerate(word[1:-1], 1) if c in _VOWELS]
            if vowel_positions:
                pos = self.rng.choice(vowel_positions)
                word = word[:pos] + word[pos + 1:]
        words[idx] = word
        return " ".join(words)

    def _weighted_pick(self, mix: dict[str, float]) -> str:
        """Pick a template ID using the provided weight map."""
        ids = list(mix.keys())
        weights = [mix[i] for i in ids]
        return self.rng.choices(ids, weights=weights, k=1)[0]
