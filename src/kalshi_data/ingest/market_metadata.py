"""Backfill historical market titles, strikes, and rule text per deployment series."""

from __future__ import annotations

import argparse
import json
import os

import polars as pl

from ..core.client import KalshiClient
from ..core.paths import CHECKPOINTS, MARKET_METADATA, SERIES


CHECKPOINT = CHECKPOINTS / "market_metadata_done.json"
ENDPOINTS = ("/historical/markets", "/markets")
FLUSH_ROWS = 150_000


def metadata_row(market: dict, series: dict) -> dict:
    return {
        "ticker": market.get("ticker"),
        "event_ticker": market.get("event_ticker"),
        "series_ticker": series.get("ticker"),
        "category": series.get("category"),
        "tier": series.get("tier"),
        "title": market.get("title"),
        "yes_sub_title": market.get("yes_sub_title"),
        "no_sub_title": market.get("no_sub_title"),
        "market_type": market.get("market_type"),
        "strike_type": market.get("strike_type"),
        "floor_strike": market.get("floor_strike"),
        "cap_strike": market.get("cap_strike"),
        "custom_strike": json.dumps(market.get("custom_strike"), sort_keys=True),
        "rules_primary": market.get("rules_primary"),
        "rules_secondary": market.get("rules_secondary"),
        "settled_time": market.get("settlement_ts") or market.get("settled_time"),
        "expiration_value": market.get("expiration_value"),
        "settlement_value_dollars": market.get("settlement_value_dollars"),
    }


def fetch_series_metadata(client: KalshiClient, series: dict) -> list[dict]:
    seen: dict[str, dict] = {}
    for endpoint in ENDPOINTS:
        for page in client.paginate(
            endpoint, "markets", status="settled", series_ticker=series["ticker"]
        ):
            for market in page:
                row = metadata_row(market, series)
                if row["ticker"]:
                    seen.setdefault(row["ticker"], row)
    return list(seen.values())


def _load_state() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {"done": [], "part": 0}


def _save_state(state: dict) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT.with_name(f".{CHECKPOINT.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(CHECKPOINT)


def _flush(rows: list[dict], state: dict) -> None:
    if not rows:
        return
    MARKET_METADATA.mkdir(parents=True, exist_ok=True)
    frame = pl.DataFrame(rows, infer_schema_length=None).unique(subset="ticker", keep="first")
    path = MARKET_METADATA / f"part-{state['part']:04d}.parquet"
    frame.write_parquet(path)
    state["part"] += 1
    print(f"metadata: {len(frame):,} rows -> {path.name}", flush=True)


def run(tier: str = "deployment", rps: float = 8.0) -> None:
    series = pl.read_parquet(SERIES).filter(pl.col("tier") == tier).sort("ticker")
    state = _load_state()
    done = set(state["done"])
    todo = [row for row in series.iter_rows(named=True) if row["ticker"] not in done]
    print(f"metadata: {len(todo):,} {tier} series pending", flush=True)
    client = KalshiClient(rps=rps)
    pending: list[dict] = []
    for index, meta in enumerate(todo, start=1):
        pending.extend(fetch_series_metadata(client, meta))
        state["done"].append(meta["ticker"])
        if len(pending) >= FLUSH_ROWS:
            _flush(pending, state)
            _save_state(state)
            pending = []
        if index % 100 == 0:
            print(f"  {index:,}/{len(todo):,} series; {len(pending):,} rows pending", flush=True)
    _flush(pending, state)
    _save_state(state)
    print("metadata: complete", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", default="deployment", choices=["deployment", "instrumentation", "review"])
    parser.add_argument("--rps", default=8.0, type=float)
    args = parser.parse_args()
    run(args.tier, args.rps)
