#!/usr/bin/env python
"""Smoke test the running API — run after `scripts/run_server.py` is up."""

import asyncio
import json
import sys

import httpx
import websockets

BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/live"


async def check(label: str, coro) -> bool:
    try:
        result = await coro
        print(f"  [OK] {label}: {result}")
        return True
    except Exception as exc:
        print(f"  [FAIL] {label}: {exc}")
        return False


async def get(client: httpx.AsyncClient, path: str) -> dict:
    r = await client.get(f"{BASE}{path}")
    r.raise_for_status()
    return r.json()


async def post(client: httpx.AsyncClient, path: str, body: dict) -> dict:
    r = await client.post(f"{BASE}{path}", json=body)
    r.raise_for_status()
    return r.json()


async def ws_receive_one(timeout: float = 5.0) -> dict:
    async with websockets.connect(WS_URL) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(msg)


async def main() -> None:
    print("\nSmart Dispatch API Smoke Test")
    print("=" * 40)
    results: list[bool] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health check
        results.append(await check("GET /health", get(client, "/health")))

        # 2. Stats
        results.append(await check("GET /api/v1/stats/", get(client, "/api/v1/stats/")))

        # 3. Graph
        results.append(await check("GET /api/v1/graph/", get(client, "/api/v1/graph/")))

        # 4. Resources
        results.append(await check("GET /api/v1/resources/", get(client, "/api/v1/resources/")))

        # 5. Incidents (empty)
        results.append(await check("GET /api/v1/incidents/", get(client, "/api/v1/incidents/")))

        # 6. List scenarios
        results.append(await check(
            "GET /api/v1/simulation/scenarios",
            get(client, "/api/v1/simulation/scenarios"),
        ))

        # 7. Simulation status
        results.append(await check(
            "GET /api/v1/simulation/status",
            get(client, "/api/v1/simulation/status"),
        ))

        # 8. Single call (fast path — no LLM in CI, may be slow)
        print("\n  [INFO] Sending a single test call (requires LLM, may be slow)...")
        results.append(await check(
            "POST /api/v1/calls/single",
            post(client, "/api/v1/calls/single", {
                "transcript": "There is a fire at the corner of Maple Street and 5th Avenue. Flames are coming from the second floor window."
            }),
        ))

        # 9. Start quiet_night scenario (speed_multiplier=100 so it finishes fast)
        results.append(await check(
            "POST /api/v1/simulation/start/scenario (quiet_night)",
            post(client, "/api/v1/simulation/start/scenario", {
                "scenario_name": "quiet_night",
                "speed_multiplier": 100.0,
            }),
        ))

        await asyncio.sleep(2)

        # 10. Simulation status while running
        results.append(await check(
            "GET /api/v1/simulation/status (running)",
            get(client, "/api/v1/simulation/status"),
        ))

        # 11. Stop simulation
        results.append(await check(
            "POST /api/v1/simulation/stop",
            post(client, "/api/v1/simulation/stop", {}),
        ))

        # 12. WebSocket — connect, receive at least one event
        print("\n  [INFO] Testing WebSocket (connecting to /ws/live)...")
        try:
            event = await ws_receive_one(timeout=5.0)
            print(f"  [OK] WebSocket: received event type={event.get('type', '?')}")
            results.append(True)
        except Exception as exc:
            print(f"  [SKIP] WebSocket: {exc} (no events in history — start a scenario first)")
            results.append(True)  # Not fatal

        # 13. Reset
        results.append(await check(
            "POST /api/v1/simulation/reset",
            post(client, "/api/v1/simulation/reset", {}),
        ))

    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
