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

ROOT = Path(__file__).resolve().parents[3]
KEY_DIR = Path.home() / ".kalshi"
BASE = "https://api.elections.kalshi.com"
API_PREFIX = "/trade-api/v2"


def _env_file() -> dict:
    out = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def find_credentials() -> tuple[str, Path] | None:
    """(key_id, pem_path). Sources, in order: repo .env + kalshi.pem
    (both gitignored), then ~/.kalshi/key_id + ~/.kalshi/kalshi.pem."""
    import os

    env = {**_env_file(), **os.environ}
    key_id = env.get("KALSHI_KEY_ID", "").strip()
    pem = Path(env.get("KALSHI_PRIVATE_KEY_PATH", "")) if env.get("KALSHI_PRIVATE_KEY_PATH") else ROOT / "kalshi.pem"
    if key_id and pem.exists():
        return key_id, pem
    if (KEY_DIR / "key_id").exists() and (KEY_DIR / "kalshi.pem").exists():
        return (KEY_DIR / "key_id").read_text().strip(), KEY_DIR / "kalshi.pem"
    return None


def credentials_present() -> bool:
    return find_credentials() is not None


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

        creds = find_credentials()
        if creds is None:
            raise FileNotFoundError(
                "no credentials: expected KALSHI_KEY_ID in .env + kalshi.pem in the "
                "project folder (or ~/.kalshi/key_id + ~/.kalshi/kalshi.pem)"
            )
        self._key_id, pem_path = creds
        self._pk = serialization.load_pem_private_key(pem_path.read_bytes(), password=None)
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
