"""Rate-limited client for Kalshi's public trade API (no auth required for market data)."""

from __future__ import annotations

import time
import threading
from collections.abc import Iterator

import httpx

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
MAX_RETRIES = 8


class SharedRateGate:
    """Thread-safe start-rate limiter shared by concurrent clients."""

    def __init__(self, rps: float):
        self._min_interval = 1.0 / rps
        self._last_request = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            delay = self._min_interval - (time.monotonic() - self._last_request)
            if delay > 0:
                time.sleep(delay)
            self._last_request = time.monotonic()


class KalshiClient:
    def __init__(
        self,
        rps: float = 5.0,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        rate_gate: SharedRateGate | None = None,
    ):
        self._min_interval = 1.0 / rps
        self._last_request = 0.0
        self._rate_gate = rate_gate
        self._http = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"User-Agent": "kalshi-structure-research/0.1"},
            transport=transport,
        )

    def get(self, path: str, **params) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        for attempt in range(MAX_RETRIES):
            if self._rate_gate is not None:
                self._rate_gate.wait()
            else:
                wait = self._min_interval - (time.monotonic() - self._last_request)
                if wait > 0:
                    time.sleep(wait)
                self._last_request = time.monotonic()
            try:
                resp = self._http.get(path, params=params)
            except httpx.TransportError:
                time.sleep(min(2**attempt, 30))
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(min(2**attempt, 30))
                continue
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError(f"GET {path} still failing after {MAX_RETRIES} attempts")

    def paginate(self, path: str, list_key: str, limit: int = 1000, **params) -> Iterator[list[dict]]:
        """Yield pages of items, following cursor pagination to exhaustion."""
        cursor = None
        while True:
            page = self.get(path, limit=limit, cursor=cursor, **params)
            items = page.get(list_key) or []
            if items:
                yield items
            cursor = page.get("cursor")
            if not cursor or not items:
                return
