"""Authenticated Kalshi client - READ-ONLY by design.

Credentials live OUTSIDE the repo, placed by the operator only:
  ~/.kalshi/key_id      - the API key id (one line)
  ~/.kalshi/kalshi.pem  - the RSA private key Kalshi generated

This module only ever issues GET requests; there is deliberately no method
that could place, amend, or cancel an order. Order execution stays with the
operator in Kalshi Pro, permanently. Never log or print key material.

Kalshi auth: each request carries KALSHI-ACCESS-KEY, KALSHI-ACCESS-TIMESTAMP
(ms epoch), and KALSHI-ACCESS-SIGNATURE = base64(RSA-PSS-SHA256 over
timestamp + METHOD + path-without-query).
"""

from __future__ import annotations

import base64
import datetime as dt
import time
from pathlib import Path

import httpx

KEY_DIR = Path.home() / ".kalshi"
KEY_ID_FILE = KEY_DIR / "key_id"
PEM_FILE = KEY_DIR / "kalshi.pem"
BASE = "https://api.elections.kalshi.com"
API_PREFIX = "/trade-api/v2"


def credentials_present() -> bool:
    return KEY_ID_FILE.exists() and PEM_FILE.exists()


def sign(private_key, timestamp_ms: str, method: str, path: str) -> str:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    msg = f"{timestamp_ms}{method}{path}".encode()
    sig = private_key.sign(
        msg,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=hashes.SHA256().digest_size),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode()


class KalshiAuthedClient:
    """Signed GETs against the portfolio endpoints. Nothing else."""

    def __init__(self, rps: float = 4.0, timeout: float = 30.0):
        from cryptography.hazmat.primitives import serialization

        if not credentials_present():
            raise FileNotFoundError(
                f"no credentials: expected {KEY_ID_FILE} and {PEM_FILE} (operator-placed)"
            )
        self._key_id = KEY_ID_FILE.read_text().strip()
        self._pk = serialization.load_pem_private_key(PEM_FILE.read_bytes(), password=None)
        self._min_interval = 1.0 / rps
        self._last = 0.0
        self._http = httpx.Client(base_url=BASE, timeout=timeout)

    def get(self, path: str, **params) -> dict:
        params = {k: v for k, v in params.items() if v is not None}
        full_path = API_PREFIX + path
        for attempt in range(6):
            wait = self._min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            ts = str(int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000))
            headers = {
                "KALSHI-ACCESS-KEY": self._key_id,
                "KALSHI-ACCESS-TIMESTAMP": ts,
                "KALSHI-ACCESS-SIGNATURE": sign(self._pk, ts, "GET", full_path),
            }
            try:
                r = self._http.get(full_path, params=params, headers=headers)
            except httpx.TransportError:
                time.sleep(min(2**attempt, 20))
                continue
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(min(2**attempt, 20))
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"GET {path} failing after retries")
