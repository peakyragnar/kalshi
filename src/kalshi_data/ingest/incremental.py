"""Daily incremental ingest: keep the settled-market corpus current.

Strategy: refresh the series catalog (new series appear constantly), then walk
the global settled feed from the high-water mark minus a 48h overlap, skipping
parlays and non-deployment tiers client-side, deduping the overlap against
markets already stored. New trade-eligible markets get their tape pulled.
Finishes by rebuilding the derived snapshot table.

The global feed includes the KXMVE parlay flood (~500k rows/day) but at
1000/page that is ~80 seconds of pagination per day of catch-up - cheaper and
more complete than per-series polling, and it automatically catches markets
from series created after the last catalog snapshot.
"""

from __future__ import annotations

import datetime as dt
import json
import os

import polars as pl

from ..analysis import derive
from . import series as ingest_series
from ..core.client import KalshiClient
from .trades import MIN_LIFETIME_DAYS, MIN_VOLUME, fetch_market_trades
from ..core.parse import market_row
from ..core.tiers import classify

from ..core.paths import CHECKPOINTS, MARKETS, TRADES

CHECKPOINT = CHECKPOINTS / "incremental.json"
OVERLAP_HOURS = 48
BACKFILL_END = "2026-07-15T00:00:00+00:00"


def write_merged_partition(df: pl.DataFrame, path, key: str) -> pl.DataFrame:
    """Atomically merge a same-day increment instead of replacing prior rows.

    The daily filename is intentionally stable, so manual recovery runs and
    launchd retries on the same UTC date must be idempotent.
    """
    if path.exists():
        df = pl.concat([pl.read_parquet(path), df], how="diagonal_relaxed")
    df = df.unique(subset=key, keep="last")
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    df.write_parquet(tmp)
    tmp.replace(path)
    return df


def select_new_rows(
    page: list[dict], series_meta: dict[str, dict], existing: set[str]
) -> list[dict]:
    """Deployment-tier, non-parlay, not-already-stored rows from a feed page."""
    out = []
    for m in page:
        ticker = m.get("ticker") or ""
        if ticker in existing:
            continue
        st = m.get("event_ticker", "").split("-")[0] if not m.get("series_ticker") else m["series_ticker"]
        meta = series_meta.get(st)
        tier = meta["tier"] if meta else classify(ticker, None)
        if tier != "deployment":
            continue
        row = market_row(m, meta or {"ticker": st, "tier": tier})
        out.append(row)
    return out


def run(rps: float = 8.0) -> None:
    series_df = ingest_series.run(KalshiClient(rps=rps))
    series_meta = {r["ticker"]: r for r in series_df.iter_rows(named=True)}

    state = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.exists() else {"high_water": BACKFILL_END}
    start = dt.datetime.fromisoformat(state["high_water"]) - dt.timedelta(hours=OVERLAP_HOURS)
    now = dt.datetime.now(dt.timezone.utc)

    existing = set(
        pl.scan_parquet(MARKETS / "*.parquet")
        .filter(
            pl.col("close_time").str.to_datetime(time_zone="UTC", strict=False)
            >= start - dt.timedelta(hours=24)
        )
        .select("ticker")
        .collect()["ticker"]
        .to_list()
    )

    client = KalshiClient(rps=rps)
    rows: list[dict] = []
    pages = 0
    for page in client.paginate(
        "/markets", "markets", status="settled",
        min_close_ts=int(start.timestamp()), max_close_ts=int(now.timestamp()),
    ):
        rows.extend(select_new_rows(page, series_meta, existing))
        pages += 1
        if pages % 100 == 0:
            print(f"  {pages} pages walked, {len(rows):,} new deployment markets", flush=True)

    if rows:
        df = pl.DataFrame(rows, infer_schema_length=None).unique(subset="ticker")
        path = MARKETS / f"incr-{now:%Y%m%d}.parquet"
        n_new = len(df)
        stored = write_merged_partition(df, path, "ticker")
        print(
            f"markets: +{n_new:,} ({len(stored):,} in today's partition) -> {path.name}",
            flush=True,
        )

        eligible = df.with_columns(
            pl.col("open_time").str.to_datetime(time_zone="UTC", strict=False),
            pl.col("close_time").str.to_datetime(time_zone="UTC", strict=False),
            pl.col("expiration_time").str.to_datetime(time_zone="UTC", strict=False),
        ).with_columns(
            pl.max_horizontal("expiration_time", "close_time").alias("end_time")
        ).filter(
            (pl.col("volume") >= MIN_VOLUME)
            & ((pl.col("end_time") - pl.col("open_time")).dt.total_days() >= MIN_LIFETIME_DAYS)
        )
        trades: list[dict] = []
        for m in eligible.iter_rows(named=True):
            trades.extend(fetch_market_trades(client, m["ticker"], m["open_time"], m["end_time"]))
        if trades:
            tdf = pl.DataFrame(trades, infer_schema_length=None).unique(subset="trade_id")
            tpath = TRADES / f"incr-{now:%Y%m%d}.parquet"
            n_new_trades = len(tdf)
            stored_trades = write_merged_partition(tdf, tpath, "trade_id")
            print(
                f"trades: +{n_new_trades:,} ({len(stored_trades):,} in today's partition) "
                f"for {len(eligible):,} eligible markets -> {tpath.name}",
                flush=True,
            )
    else:
        print("no new deployment markets in window", flush=True)

    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps({"high_water": now.isoformat()}))
    derive.run()
    print(f"incremental complete; high water -> {now:%Y-%m-%d %H:%M}", flush=True)


if __name__ == "__main__":
    run()
