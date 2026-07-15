"""Backfill the trade tape per market, for markets that can contribute snapshots.

Data-availability facts (probed 2026-07-15):
- /series/{s}/markets/{t}/candlesticks 404s for markets settled before the
  historical cutoff (2026-05-16), so candles cannot supply deep history.
- /historical/trades?ticker=X serves the full pre-cutoff tape with taker side;
  /markets/trades serves post-cutoff. Trades are therefore the primary price
  source for every era.

Only markets with lifetime >= MIN_LIFETIME_DAYS are fetched: the shortest
snapshot horizon is T-7d, so a market that lived less than ~a week can never
contribute a snapshot row and its tape buys nothing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import polars as pl

from .client import KalshiClient
from .parse import cents, quantity

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TRADES_DIR = DATA_DIR / "trades"
CHECKPOINT = DATA_DIR / "checkpoints" / "trades_done.json"
FLUSH_ROWS = 500_000

CUTOFF = dt.datetime(2026, 5, 16, tzinfo=dt.timezone.utc)
MIN_LIFETIME_DAYS = 6.0
MIN_VOLUME = 1.0


def trade_row(t: dict) -> dict:
    return {
        "ticker": t.get("ticker"),
        "trade_id": t.get("trade_id"),
        "created_time": t.get("created_time"),
        "yes_price_cents": cents(t, "yes_price"),
        "count": quantity(t, "count"),
        "taker_side": t.get("taker_side"),
        "is_block_trade": t.get("is_block_trade"),
    }


def fetch_market_trades(
    client: KalshiClient, ticker: str, open_time: dt.datetime, end_time: dt.datetime
) -> list[dict]:
    endpoints = []
    if open_time < CUTOFF:
        endpoints.append("/historical/trades")
    if end_time >= CUTOFF:
        endpoints.append("/markets/trades")
    seen: dict[str, dict] = {}
    for ep in endpoints:
        for page in client.paginate(ep, "trades", ticker=ticker):
            for t in page:
                row = trade_row(t)
                if row["trade_id"]:
                    seen.setdefault(row["trade_id"], row)
    return list(seen.values())


def eligible_markets(tier: str) -> pl.DataFrame:
    df = pl.read_parquet(DATA_DIR / "markets" / "*.parquet")
    df = df.with_columns(
        pl.col("open_time").str.to_datetime(time_zone="UTC", strict=False),
        pl.col("close_time").str.to_datetime(time_zone="UTC", strict=False),
        pl.col("expiration_time").str.to_datetime(time_zone="UTC", strict=False),
    ).with_columns(
        pl.max_horizontal("expiration_time", "close_time").alias("end_time")
    )
    return df.filter(
        (pl.col("tier") == tier)
        & (pl.col("volume") >= MIN_VOLUME)
        & ((pl.col("end_time") - pl.col("open_time")).dt.total_days() >= MIN_LIFETIME_DAYS)
    ).select("ticker", "open_time", "end_time")


def _load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {"done": [], "part": 0}


def run(tier: str, rps: float = 6.0) -> None:
    markets = eligible_markets(tier)
    client = KalshiClient(rps=rps)
    state = _load_checkpoint()
    done = set(state["done"])
    todo = [m for m in markets.iter_rows(named=True) if m["ticker"] not in done]
    print(f"tier={tier}: {len(todo):,} markets need trades ({len(done):,} done)", flush=True)

    pending: list[dict] = []
    for i, m in enumerate(todo):
        pending.extend(fetch_market_trades(client, m["ticker"], m["open_time"], m["end_time"]))
        state["done"].append(m["ticker"])
        if len(pending) >= FLUSH_ROWS:
            TRADES_DIR.mkdir(parents=True, exist_ok=True)
            df = pl.DataFrame(pending, infer_schema_length=None).unique(subset="trade_id")
            path = TRADES_DIR / f"part-{state['part']:04d}.parquet"
            df.write_parquet(path)
            state["part"] += 1
            CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
            CHECKPOINT.write_text(json.dumps(state))
            print(f"flushed {len(df):,} trades -> {path.name}", flush=True)
            pending = []
        if (i + 1) % 500 == 0:
            print(f"  {i + 1:,}/{len(todo):,} markets, {len(pending):,} trades pending", flush=True)

    if pending:
        TRADES_DIR.mkdir(parents=True, exist_ok=True)
        df = pl.DataFrame(pending, infer_schema_length=None).unique(subset="trade_id")
        path = TRADES_DIR / f"part-{state['part']:04d}.parquet"
        df.write_parquet(path)
        state["part"] += 1
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(state))
    print(f"tier={tier}: trades complete", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", required=True, choices=["deployment", "instrumentation"])
    ap.add_argument("--rps", type=float, default=6.0)
    args = ap.parse_args()
    run(tier=args.tier, rps=args.rps)
