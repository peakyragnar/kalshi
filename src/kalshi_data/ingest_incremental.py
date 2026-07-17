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
from pathlib import Path

import polars as pl

from . import derive, ingest_series
from .client import KalshiClient
from .ingest_trades import MIN_LIFETIME_DAYS, MIN_VOLUME, fetch_market_trades
from .parse import market_row
from .tiers import classify

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CHECKPOINT = DATA_DIR / "checkpoints" / "incremental.json"
OVERLAP_HOURS = 48
BACKFILL_END = "2026-07-15T00:00:00+00:00"


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
        pl.scan_parquet(DATA_DIR / "markets" / "*.parquet")
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
        path = DATA_DIR / "markets" / f"incr-{now:%Y%m%d}.parquet"
        df.write_parquet(path)
        print(f"markets: +{len(df):,} -> {path.name}", flush=True)

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
            tpath = DATA_DIR / "trades" / f"incr-{now:%Y%m%d}.parquet"
            tdf.write_parquet(tpath)
            print(f"trades: +{len(tdf):,} for {len(eligible):,} eligible markets -> {tpath.name}", flush=True)
    else:
        print("no new deployment markets in window", flush=True)

    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps({"high_water": now.isoformat()}))
    derive.run()
    print(f"incremental complete; high water -> {now:%Y-%m-%d %H:%M}", flush=True)


if __name__ == "__main__":
    run()
