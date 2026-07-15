"""Backfill settled markets per series, live + historical endpoints, with resume.

Walks series from data/series.parquet (skipping tier=excluded), queries
/markets and /historical/markets with a series_ticker filter - which is what
makes the backfill tractable: it never touches the KXMVE* parlay flood.

Output: data/markets/part-NNNN.parquet, checkpoint in data/checkpoints/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from .client import KalshiClient
from .parse import market_row

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MARKETS_DIR = DATA_DIR / "markets"
CHECKPOINT = DATA_DIR / "checkpoints" / "markets_done.json"
FLUSH_ROWS = 150_000

ENDPOINTS = ("/markets", "/historical/markets")


def _load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {"done": [], "part": 0}


def _save_checkpoint(state: dict) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(state))


def _flush(rows: list[dict], state: dict) -> None:
    if not rows:
        return
    MARKETS_DIR.mkdir(parents=True, exist_ok=True)
    df = pl.DataFrame(rows, infer_schema_length=None).unique(subset="ticker", keep="first")
    path = MARKETS_DIR / f"part-{state['part']:04d}.parquet"
    df.write_parquet(path)
    print(f"flushed {len(df):,} rows -> {path.name}", flush=True)
    state["part"] += 1


def fetch_series_markets(client: KalshiClient, series_meta: dict) -> list[dict]:
    seen: dict[str, dict] = {}
    for endpoint in ENDPOINTS:
        for page in client.paginate(
            endpoint, "markets", status="settled", series_ticker=series_meta["ticker"]
        ):
            for m in page:
                row = market_row(m, series_meta)
                if row["ticker"]:
                    seen.setdefault(row["ticker"], row)
    return list(seen.values())


def run(tier: str, rps: float = 6.0) -> None:
    series = pl.read_parquet(DATA_DIR / "series.parquet").filter(pl.col("tier") == tier)
    client = KalshiClient(rps=rps)
    state = _load_checkpoint()
    done = set(state["done"])
    pending: list[dict] = []
    todo = [s for s in series.iter_rows(named=True) if s["ticker"] not in done]
    print(f"tier={tier}: {len(todo):,} series to fetch ({len(done):,} already done)", flush=True)

    for i, s in enumerate(todo):
        pending.extend(fetch_series_markets(client, s))
        state["done"].append(s["ticker"])
        if len(pending) >= FLUSH_ROWS:
            _flush(pending, state)
            _save_checkpoint(state)
            pending = []
        if (i + 1) % 100 == 0:
            print(f"  {i + 1:,}/{len(todo):,} series, {len(pending):,} rows pending", flush=True)

    _flush(pending, state)
    _save_checkpoint(state)
    print(f"tier={tier}: complete", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", required=True, choices=["deployment", "instrumentation", "review"])
    ap.add_argument("--rps", type=float, default=6.0)
    args = ap.parse_args()
    run(tier=args.tier, rps=args.rps)
