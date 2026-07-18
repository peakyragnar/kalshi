"""Build the core derived table: one row per settled market per snapshot horizon.

Per phase0-assumptions.md section 5: horizons T-7/30/90/180/365d before
expiration; each snapshot carries the last traded price at or before the
snapshot instant, the timestamp of that trade (staleness), and cumulative
volume; joined to settlement outcome and fee metadata.
"""

from __future__ import annotations

import json

import polars as pl

from ..core.parquet import read_shards
from ..core.paths import DERIVED, MARKETS, RULEBOOK_VERDICTS, SERIES, TRADES
from ..core.tiers import apply_current_tiers
from .research_panel import exclude_red_rulebooks
HORIZONS_DAYS = (7, 30, 90, 180, 365)


def build_snapshots(markets: pl.DataFrame, trades: pl.DataFrame) -> pl.DataFrame:
    """Pure core: markets has parsed datetime columns open_time/close_time/
    expiration_time plus metadata; trades has ticker/created_time/
    yes_price_cents/count with created_time parsed."""
    markets = markets.with_columns(
        # close_time is the last tradable instant. expiration_time may be a
        # rescheduling ceiling a week later and must not anchor entry horizons.
        pl.coalesce(pl.col("close_time"), pl.col("expiration_time")).alias("end_time"),
        pl.coalesce(pl.col("settled_time"), pl.col("close_time"), pl.col("expiration_time")).alias(
            "resolve_time"
        ),
    )

    trades = trades.sort("ticker", "created_time").with_columns(
        pl.col("count").cum_sum().over("ticker").alias("cum_volume")
    )

    frames = []
    for h in HORIZONS_DAYS:
        snap = (
            markets.with_columns(
                (pl.col("end_time") - pl.duration(days=h)).alias("snap_ts"),
                pl.lit(h).alias("horizon_days"),
            )
            .filter(pl.col("open_time") <= pl.col("snap_ts"))
            .sort("snap_ts")
        )
        if len(snap) == 0:
            continue
        joined = snap.join_asof(
            trades.sort("created_time").rename({"created_time": "trade_ts"}),
            left_on="snap_ts",
            right_on="trade_ts",
            by="ticker",
            strategy="backward",
        )
        frames.append(joined)

    out = pl.concat(frames, how="vertical_relaxed")
    return (
        out.filter(pl.col("yes_price_cents").is_not_null())
        .with_columns(
            (pl.col("snap_ts") - pl.col("trade_ts")).dt.total_seconds().alias("staleness_s"),
            (pl.col("resolve_time") - pl.col("snap_ts")).dt.total_days().alias("hold_days"),
            (pl.col("result") == "yes").cast(pl.Int8).alias("result_yes"),
        )
        .select(
            "ticker",
            "series_ticker",
            "event_ticker",
            "category",
            "tier",
            "fee_type",
            "fee_multiplier",
            "horizon_days",
            "snap_ts",
            "yes_price_cents",
            "trade_ts",
            "staleness_s",
            "cum_volume",
            "hold_days",
            "result",
            "result_yes",
            "volume",
        )
    )


def run() -> None:
    markets = (
        apply_current_tiers(read_shards(MARKETS), pl.read_parquet(SERIES))
        .filter(
            (pl.col("tier") == "deployment") & pl.col("result").is_in(["yes", "no"])
        )
        .with_columns(
            pl.col("open_time").str.to_datetime(time_zone="UTC", strict=False),
            pl.col("close_time").str.to_datetime(time_zone="UTC", strict=False),
            pl.col("expiration_time").str.to_datetime(time_zone="UTC", strict=False),
            pl.col("settled_time").cast(pl.String).str.to_datetime(time_zone="UTC", strict=False),
        )
    )
    markets = exclude_red_rulebooks(
        markets, json.loads(RULEBOOK_VERDICTS.read_text())
    )
    trades = read_shards(
        TRADES, columns=["ticker", "created_time", "yes_price_cents", "count"]
    ).with_columns(pl.col("created_time").str.to_datetime(time_zone="UTC", strict=False))
    snaps = build_snapshots(markets, trades)
    out = DERIVED
    out.mkdir(parents=True, exist_ok=True)
    snaps.write_parquet(out / "snapshots.parquet")
    print(f"derived: {len(snaps):,} snapshot rows -> {out / 'snapshots.parquet'}")
    print(snaps.group_by("horizon_days").len().sort("horizon_days"))


if __name__ == "__main__":
    run()
