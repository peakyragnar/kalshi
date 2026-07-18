"""Backfill historical market titles, strikes, and rule text per deployment series."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import os
import threading

import polars as pl

from ..core.client import KalshiClient, SharedRateGate
from ..core.parquet import read_shards
from ..core.paths import CHECKPOINTS, MARKET_METADATA, MARKETS, SERIES


CHECKPOINT = CHECKPOINTS / "market_metadata_done.json"
ENDPOINTS = ("/historical/markets", "/markets")
FLUSH_ROWS = 150_000
CHECKPOINT_SERIES = 250
_thread_state = threading.local()
_shared_rate_gate: SharedRateGate | None = None


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


def fetch_series_metadata(
    client: KalshiClient, series: dict, endpoints: tuple[str, ...] = ENDPOINTS
) -> list[dict]:
    seen: dict[str, dict] = {}
    for endpoint in endpoints:
        for page in client.paginate(
            endpoint, "markets", status="settled", series_ticker=series["ticker"]
        ):
            for market in page:
                row = metadata_row(market, series)
                if row["ticker"]:
                    seen.setdefault(row["ticker"], row)
    return list(seen.values())


def fetch_market_metadata(client: KalshiClient, ticker: str, series: dict) -> dict | None:
    for endpoint in (f"/markets/{ticker}", f"/historical/markets/{ticker}"):
        try:
            payload = client.get(endpoint)
        except Exception:
            continue
        market = payload.get("market")
        if market:
            return metadata_row(market, series)
    return None


def _load_state() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text())
    return {"done": [], "part": 0}


def _save_state(state: dict) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    tmp = CHECKPOINT.with_name(f".{CHECKPOINT.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(CHECKPOINT)


def normalize_metadata_frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows, infer_schema_length=None).with_columns(
        pl.col("floor_strike").cast(pl.Float64, strict=False),
        pl.col("cap_strike").cast(pl.Float64, strict=False),
    ).unique(subset="ticker", keep="first")


def metadata_gaps(
    raw: pl.DataFrame, stored: pl.DataFrame, deployment_series: pl.DataFrame
) -> pl.DataFrame:
    """Return missing raw tickers only when their current series is in scope."""
    return raw.join(stored, on="ticker", how="anti").join(
        deployment_series.rename({"ticker": "series_ticker"}),
        on="series_ticker",
        how="inner",
    )


def _flush(rows: list[dict], state: dict) -> None:
    if not rows:
        return
    MARKET_METADATA.mkdir(parents=True, exist_ok=True)
    frame = normalize_metadata_frame(rows)
    path = MARKET_METADATA / f"part-{state['part']:04d}.parquet"
    frame.write_parquet(path)
    state["part"] += 1
    print(f"metadata: {len(frame):,} rows -> {path.name}", flush=True)


def _fetch_worker(series: dict, per_worker_rps: float) -> tuple[str, list[dict]]:
    client = getattr(_thread_state, "client", None)
    if client is None:
        client = KalshiClient(rps=per_worker_rps, rate_gate=_shared_rate_gate)
        _thread_state.client = client
    endpoints = ENDPOINTS if series.get("needs_live_endpoint") else ("/historical/markets",)
    return series["ticker"], fetch_series_metadata(client, series, endpoints)


def run(tier: str = "deployment", rps: float = 4.0, workers: int = 8) -> None:
    global _shared_rate_gate
    _shared_rate_gate = SharedRateGate(rps)
    series = pl.read_parquet(SERIES).filter(pl.col("tier") == tier).sort("ticker")
    recent_cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=90)
    market_recency = pl.scan_parquet(MARKETS / "*.parquet").group_by("series_ticker").agg(
        pl.coalesce("close_time", "expiration_time").max().alias("latest_market_time"),
        pl.len().alias("market_count"),
    ).collect().with_columns(
        pl.col("latest_market_time").str.to_datetime(time_zone="UTC", strict=False)
    ).with_columns(
        (pl.col("latest_market_time") >= recent_cutoff).alias("needs_live_endpoint")
    ).rename({"series_ticker": "ticker"}).select(
        "ticker", "needs_live_endpoint", "market_count"
    )
    series = series.join(market_recency, on="ticker", how="left").with_columns(
        pl.col("needs_live_endpoint").fill_null(False),
        pl.col("market_count").fill_null(0),
    )
    state = _load_state()
    done = set(state["done"])
    todo = [row for row in series.iter_rows(named=True) if row["ticker"] not in done]
    print(f"metadata: {len(todo):,} {tier} series pending", flush=True)
    large = [meta for meta in todo if meta["market_count"] >= 10_000]
    small = [meta for meta in todo if meta["market_count"] < 10_000]
    if large:
        print(f"metadata: {len(large)} large series processed serially", flush=True)
    serial_client = KalshiClient(rps=rps, rate_gate=_shared_rate_gate)
    for index, meta in enumerate(large, start=1):
        endpoints = ENDPOINTS if meta["needs_live_endpoint"] else ("/historical/markets",)
        rows = fetch_series_metadata(serial_client, meta, endpoints)
        state["done"].append(meta["ticker"])
        _flush(rows, state)
        _save_state(state)
        print(f"  large {index}/{len(large)}: {meta['ticker']} ({len(rows):,} rows)", flush=True)

    pending: list[dict] = []
    per_worker_rps = max(rps / workers, 0.25)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(
            lambda meta: _fetch_worker(meta, per_worker_rps), small,
        )
        for index, (ticker, rows) in enumerate(results, start=1):
            pending.extend(rows)
            state["done"].append(ticker)
            if len(pending) >= FLUSH_ROWS or index % CHECKPOINT_SERIES == 0:
                _flush(pending, state)
                _save_state(state)
                pending = []
            if index % 100 == 0:
                print(f"  {index:,}/{len(small):,} small series; {len(pending):,} rows pending", flush=True)
    _flush(pending, state)
    _save_state(state)
    raw = read_shards(MARKETS, columns=["ticker", "series_ticker"]).unique("ticker")
    stored = pl.read_parquet(MARKET_METADATA / "*.parquet", columns=["ticker"]).unique("ticker")
    missing = metadata_gaps(raw, stored, series)
    if len(missing):
        print(f"metadata: repairing {len(missing):,} ticker-level gaps", flush=True)
        repair_client = KalshiClient(rps=rps, rate_gate=_shared_rate_gate)
        repaired = []
        for row in missing.iter_rows(named=True):
            value = fetch_market_metadata(repair_client, row["ticker"], row)
            if value:
                repaired.append(value)
        _flush(repaired, state)
        _save_state(state)
        print(f"metadata: repaired {len(repaired):,}/{len(missing):,} gaps", flush=True)
    print("metadata: complete", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", default="deployment", choices=["deployment", "instrumentation", "review"])
    parser.add_argument("--rps", default=4.0, type=float)
    parser.add_argument("--workers", default=8, type=int)
    args = parser.parse_args()
    run(args.tier, args.rps, args.workers)
