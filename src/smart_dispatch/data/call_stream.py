"""Async streaming interface for 112 calls."""

import asyncio
from datetime import datetime
from typing import AsyncIterator, Optional

from smart_dispatch.data.call_generator import MockCallGenerator
from smart_dispatch.data.schemas import MockCall


class CallStream:
    """Async iterator that yields :class:`MockCall` objects at a configurable rate.

    Two construction modes:

    * **Live mode** (default via ``__init__``): generates calls on-the-fly at
      ``calls_per_minute`` with optional jitter.
    * **Replay mode** (via :meth:`from_batch`): replays a pre-generated batch
      honouring real timestamp deltas, scaled by ``speed_multiplier``.

    Args:
        generator: A :class:`MockCallGenerator` used in live mode.
        calls_per_minute: Target call rate.
        jitter: 0–1 fraction added to inter-call delay randomness.
        max_calls: Stop after this many calls (``None`` = infinite).
        duplicate_ratio: Fraction of live-mode calls that are duplicates.
    """

    def __init__(
        self,
        generator: MockCallGenerator,
        calls_per_minute: float = 30.0,
        jitter: float = 0.3,
        max_calls: Optional[int] = None,
        duplicate_ratio: float = 0.3,
    ) -> None:
        self._generator = generator
        self._calls_per_minute = calls_per_minute
        self._jitter = max(0.0, min(1.0, jitter))
        self._max_calls = max_calls
        self._duplicate_ratio = duplicate_ratio
        self._replay_calls: Optional[list[MockCall]] = None
        self._speed_multiplier: float = 1.0

    @classmethod
    def from_batch(
        cls,
        calls: list[MockCall],
        speed_multiplier: float = 1.0,
    ) -> "CallStream":
        """Replay a pre-generated batch using each call's actual timestamps.

        Args:
            calls: Pre-generated calls (need not be sorted).
            speed_multiplier: Scale factor for time deltas.  ``10.0`` means
                10 minutes of real-time calls replay in 1 minute.

        Returns:
            A :class:`CallStream` configured for replay mode.
        """
        obj = cls.__new__(cls)
        obj._generator = None  # type: ignore[assignment]
        obj._replay_calls = sorted(calls, key=lambda c: c.timestamp)
        obj._speed_multiplier = speed_multiplier
        obj._max_calls = None
        obj._jitter = 0.0
        obj._calls_per_minute = 0.0
        obj._duplicate_ratio = 0.0
        return obj

    async def __aiter__(self) -> AsyncIterator[MockCall]:
        """Yield calls, sleeping between them to simulate real-time arrival."""
        if self._replay_calls is not None:
            async for call in self._replay_iter():
                yield call
        else:
            async for call in self._live_iter():
                yield call

    # ------------------------------------------------------------------
    # Internal iterators
    # ------------------------------------------------------------------

    async def _live_iter(self) -> AsyncIterator[MockCall]:
        """Generate calls on-the-fly using the attached generator."""
        mean_delay = 60.0 / max(self._calls_per_minute, 0.001)
        emitted = 0
        # Pre-seed some event clusters for scattered duplicates
        pending_clusters: list[list[MockCall]] = []

        while self._max_calls is None or emitted < self._max_calls:
            # Decide: emit a pending duplicate or generate a new call
            if pending_clusters and self._generator.rng.random() < 0.4:
                cluster = pending_clusters[0]
                call = cluster.pop(0)
                if not cluster:
                    pending_clusters.pop(0)
            else:
                if self._generator.rng.random() < self._duplicate_ratio:
                    cluster = self._generator.generate_event_cluster(num_calls=2)
                    call = cluster[0]
                    if len(cluster) > 1:
                        pending_clusters.append(cluster[1:])
                else:
                    call = self._generator.generate_call()

            yield call
            emitted += 1

            if self._max_calls is not None and emitted >= self._max_calls:
                break

            # Sleep with jitter
            lo = mean_delay * (1.0 - self._jitter)
            hi = mean_delay * (1.0 + self._jitter)
            delay = self._generator.rng.uniform(lo, hi)
            await asyncio.sleep(delay)

    async def _replay_iter(self) -> AsyncIterator[MockCall]:
        """Replay pre-generated calls honouring timestamp deltas."""
        assert self._replay_calls is not None
        calls = self._replay_calls
        if not calls:
            return

        yield calls[0]
        for prev, curr in zip(calls, calls[1:]):
            delta_secs: float = (curr.timestamp - prev.timestamp).total_seconds()
            sleep_time = max(0.0, delta_secs / self._speed_multiplier)
            await asyncio.sleep(sleep_time)
            yield curr
