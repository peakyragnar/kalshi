"""Backfill the trade tape per market, for markets that can contribute snapshots.

Data-availability facts (probed 2026-07-15):
- /series/{s}/markets/{t}/candlesticks 404s for markets settled before the
  historical cutoff (2026-05-16), so candles cannot supply deep history.
- /historical/trades?ticker=X serves the full pre-cutoff tape with taker side;
  /markets/trades serves post-cutoff. Trades are therefore the primary price
  source for every era.

All traded deployment markets are fetched. Short-duration contracts feed the
research panel's T-1h/T-6h/T-1d/T-3d decision points even though they cannot
contribute to the legacy T-7d snapshot grid.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json

import polars as pl

from ..core.client import KalshiClient
from ..core.parse import cents, quantity

from ..core.paths import CHECKPOINTS, MARKETS, TRADES as TRADES_DIR

CHECKPOINT = CHECKPOINTS / "trades_done.json"
FLUSH_ROWS = 500_000

CUTOFF = dt.datetime(2026, 5, 16, tzinfo=dt.timezone.utc)  # outage fallback only
MIN_LIFETIME_DAYS = 0.0
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
    client: KalshiClient,
    ticker: str,
    open_time: dt.datetime,
    end_time: dt.datetime,
    trade_cutoff: dt.datetime | None = None,
) -> list[dict]:
    trade_cutoff = trade_cutoff or CUTOFF
    endpoints = []
    if open_time < trade_cutoff:
        endpoints.append("/historical/trades")
    if end_time >= trade_cutoff:
        endpoints.append("/markets/trades")
    seen: dict[str, dict] = {}
    for ep in endpoints:
        for page in client.paginate(ep, "trades", ticker=ticker):
            for t in page:
                row = trade_row(t)
                if row["trade_id"]:
                    seen.setdefault(row["trade_id"], row)
    return list(seen.values())


def trade_cutoff(client: KalshiClient) -> dt.datetime:
    """Current API partition boundary; fallback preserves recoverability."""
    try:
        raw = client.get("/historical/cutoff").get("trades_created_ts")
        if raw:
            return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception as exc:
        print(f"historical cutoff unavailable ({exc}); using fallback {CUTOFF.isoformat()}")
    return CUTOFF


def eligible_markets_from_frame(
    df: pl.DataFrame, tier: str, min_lifetime_days: float = MIN_LIFETIME_DAYS
) -> pl.DataFrame:
    df = df.with_columns(
        _as_datetime(df, "open_time"),
        _as_datetime(df, "close_time"),
        _as_datetime(df, "expiration_time"),
    ).with_columns(pl.coalesce("close_time", "expiration_time").alias("end_time"))
    return df.filter(
        (pl.col("tier") == tier)
        & (pl.col("volume") >= MIN_VOLUME)
        & (
            (pl.col("end_time") - pl.col("open_time")).dt.total_seconds()
            >= min_lifetime_days * 86400
        )
    ).select("ticker", "open_time", "end_time").sort("ticker")


def _as_datetime(df: pl.DataFrame, name: str) -> pl.Expr:
    dtype = df.schema[name]
    if dtype == pl.String:
        return pl.col(name).str.to_datetime(time_zone="UTC", strict=False)
    return pl.col(name).cast(pl.Datetime(time_zone="UTC"), strict=False)


def eligible_markets(tier: str, min_lifetime_days: float = MIN_LIFETIME_DAYS) -> pl.DataFrame:
    return eligible_markets_from_frame(
        pl.read_parquet(MARKETS / "*.parquet"), tier, min_lifetime_days
    )


def _load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {"done": [], "part": 0}


def run(tier: str, rps: float = 6.0, min_lifetime_days: float = MIN_LIFETIME_DAYS) -> None:
    markets = eligible_markets(tier, min_lifetime_days)
    client = KalshiClient(rps=rps)
    cutoff = trade_cutoff(client)
    state = _load_checkpoint()
    done = set(state["done"])
    todo = [m for m in markets.iter_rows(named=True) if m["ticker"] not in done]
    print(f"tier={tier}: {len(todo):,} markets need trades ({len(done):,} done)", flush=True)

    pending: list[dict] = []
    for i, m in enumerate(todo):
        pending.extend(
            fetch_market_trades(
                client, m["ticker"], m["open_time"], m["end_time"], trade_cutoff=cutoff
            )
        )
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
    ap.add_argument("--min-lifetime-days", type=float, default=MIN_LIFETIME_DAYS)
    args = ap.parse_args()
    run(tier=args.tier, rps=args.rps, min_lifetime_days=args.min_lifetime_days)
