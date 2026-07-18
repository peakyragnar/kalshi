"""Leakage-resistant research tables built from raw markets and trades.

Decision points contain only information observable at the decision timestamp.
Outcomes are stored separately and joined only by an explicitly registered
hypothesis runner. Unknown early-resolution timing is flagged, never inferred.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt

import polars as pl

from ..core.paths import DECISION_POINTS, MARKET_METADATA, MARKET_RELATIONS, MARKETS, OUTCOMES, TRADES


@dataclass(frozen=True)
class DecisionSpec:
    anchor: str
    label: str
    offset: dt.timedelta


DEFAULT_SPECS = (
    DecisionSpec("close", "T-1h", dt.timedelta(hours=1)),
    DecisionSpec("close", "T-6h", dt.timedelta(hours=6)),
    DecisionSpec("close", "T-1d", dt.timedelta(days=1)),
    DecisionSpec("close", "T-3d", dt.timedelta(days=3)),
    DecisionSpec("close", "T-7d", dt.timedelta(days=7)),
    DecisionSpec("close", "T-30d", dt.timedelta(days=30)),
    DecisionSpec("close", "T-90d", dt.timedelta(days=90)),
    DecisionSpec("close", "T-180d", dt.timedelta(days=180)),
    DecisionSpec("close", "T-365d", dt.timedelta(days=365)),
    DecisionSpec("listing", "L+1d", dt.timedelta(days=1)),
    DecisionSpec("listing", "L+7d", dt.timedelta(days=7)),
    DecisionSpec("listing", "L+30d", dt.timedelta(days=30)),
)


def _dt_expr(df: pl.DataFrame, name: str) -> pl.Expr:
    dtype = df.schema[name]
    if dtype == pl.String:
        return pl.col(name).str.to_datetime(time_zone="UTC", strict=False)
    return pl.col(name).cast(pl.Datetime(time_zone="UTC"), strict=False)


def normalize_market_times(markets: pl.DataFrame) -> pl.DataFrame:
    return markets.with_columns(
        *[_dt_expr(markets, c) for c in ("open_time", "close_time", "expiration_time", "settled_time")]
    ).with_columns(
        # Finalized close_time is the actual end of trading. expiration_time is
        # often only a later rescheduling ceiling.
        pl.coalesce("close_time", "expiration_time").alias("scheduled_end_time")
    )


def _decision_frames(markets: pl.DataFrame, specs: list[DecisionSpec] | tuple[DecisionSpec, ...]) -> pl.DataFrame:
    frames = []
    for spec in specs:
        delta = pl.duration(microseconds=int(spec.offset.total_seconds() * 1_000_000))
        decision = (
            pl.col("scheduled_end_time") - delta
            if spec.anchor == "close"
            else pl.col("open_time") + delta
        )
        frame = markets.with_columns(
            decision.alias("decision_time"),
            pl.lit(spec.anchor).alias("decision_anchor"),
            pl.lit(spec.label).alias("decision_label"),
            pl.lit(int(spec.offset.total_seconds())).alias("offset_seconds"),
        ).filter(
            pl.col("decision_time").is_not_null()
            & (pl.col("decision_time") >= pl.col("open_time"))
            & (pl.col("decision_time") < pl.col("scheduled_end_time"))
        )
        frames.append(frame)
    if not frames:
        return markets.head(0).with_columns(
            pl.lit(None).cast(pl.Datetime(time_zone="UTC")).alias("decision_time"),
            pl.lit(None).cast(pl.String).alias("decision_anchor"),
            pl.lit(None).cast(pl.String).alias("decision_label"),
            pl.lit(None).cast(pl.Int64).alias("offset_seconds"),
        )
    return pl.concat(frames, how="vertical_relaxed")


def build_decision_points(
    markets: pl.DataFrame,
    trades: pl.DataFrame,
    specs: list[DecisionSpec] | tuple[DecisionSpec, ...] = DEFAULT_SPECS,
) -> pl.DataFrame:
    markets = normalize_market_times(markets)
    trades = trades.with_columns(_dt_expr(trades, "created_time").alias("trade_time")).sort(
        "trade_time", "trade_id"
    )
    trade_features = trades.with_columns(
        pl.col("count").cum_sum().over("ticker").alias("cumulative_volume"),
        pl.when(pl.col("taker_side") == "yes").then(pl.col("count")).otherwise(0.0)
        .cum_sum().over("ticker").alias("cumulative_yes_taker_volume"),
        pl.when(pl.col("taker_side") == "no").then(pl.col("count")).otherwise(0.0)
        .cum_sum().over("ticker").alias("cumulative_no_taker_volume"),
    )
    points = _decision_frames(markets, specs).sort("decision_time")
    joined = points.join_asof(
        trade_features.select(
            "ticker", "trade_time", "yes_price_cents", "cumulative_volume",
            "cumulative_yes_taker_volume", "cumulative_no_taker_volume", "is_block_trade",
        ).sort("trade_time"),
        left_on="decision_time", right_on="trade_time", by="ticker", strategy="backward",
    ).filter(pl.col("yes_price_cents").is_not_null())

    starts = joined.select("ticker", "decision_time").unique().with_columns(
        (pl.col("decision_time") - pl.duration(hours=24)).alias("window_start")
    ).sort("window_start")
    before = starts.join_asof(
        trade_features.select(
            "ticker", "trade_time", "cumulative_volume", "cumulative_yes_taker_volume",
            "cumulative_no_taker_volume",
        ).rename({
            "trade_time": "window_trade_time",
            "cumulative_volume": "start_volume",
            "cumulative_yes_taker_volume": "start_yes_volume",
            "cumulative_no_taker_volume": "start_no_volume",
        }).sort("window_trade_time"),
        left_on="window_start", right_on="window_trade_time", by="ticker", strategy="backward",
    ).select("ticker", "decision_time", "start_volume", "start_yes_volume", "start_no_volume")
    joined = joined.join(before, on=["ticker", "decision_time"], how="left").with_columns(
        (pl.col("cumulative_volume") - pl.col("start_volume").fill_null(0)).alias("volume_24h"),
        (pl.col("cumulative_yes_taker_volume") - pl.col("start_yes_volume").fill_null(0)).alias("yes_taker_volume_24h"),
        (pl.col("cumulative_no_taker_volume") - pl.col("start_no_volume").fill_null(0)).alias("no_taker_volume_24h"),
        (pl.col("decision_time") - pl.col("trade_time")).dt.total_seconds().alias("price_staleness_seconds"),
        (pl.col("decision_time") - pl.col("open_time")).dt.total_seconds().alias("listing_age_seconds"),
        (pl.col("scheduled_end_time") - pl.col("decision_time")).dt.total_seconds().alias("scheduled_hold_seconds"),
        (pl.col("decision_time") < pl.col("scheduled_end_time")).alias("decision_time_trustworthy"),
    ).with_columns(
        pl.when((pl.col("yes_taker_volume_24h") + pl.col("no_taker_volume_24h")) > 0)
        .then(pl.col("yes_taker_volume_24h") / (pl.col("yes_taker_volume_24h") + pl.col("no_taker_volume_24h")))
        .otherwise(None).alias("yes_taker_share_24h")
    )
    keep = [
        "ticker", "event_ticker", "series_ticker", "category", "tier", "frequency",
        "fee_type", "fee_multiplier", "market_type", "can_close_early", "decision_anchor",
        "decision_label", "offset_seconds", "decision_time", "open_time", "scheduled_end_time",
        "yes_price_cents", "trade_time", "is_block_trade", "price_staleness_seconds",
        "listing_age_seconds", "scheduled_hold_seconds", "cumulative_volume", "volume_24h",
        "yes_taker_volume_24h", "no_taker_volume_24h", "yes_taker_share_24h",
        "decision_time_trustworthy",
    ]
    return joined.select([c for c in keep if c in joined.columns]).sort(
        "ticker", "decision_time", "decision_label"
    )


def build_outcomes(markets: pl.DataFrame) -> pl.DataFrame:
    markets = normalize_market_times(markets)
    return markets.with_columns(
        (pl.col("result") == "yes").cast(pl.Int8).alias("result_yes"),
        pl.when(pl.col("settled_time").is_not_null()).then(pl.col("settled_time"))
        .otherwise(None).alias("resolution_time"),
        pl.col("settled_time").is_not_null().alias("resolution_time_trustworthy"),
        (pl.col("scheduled_end_time") - pl.col("open_time")).dt.total_seconds().alias("scheduled_lifetime_seconds"),
    ).select(
        "ticker", "event_ticker", "series_ticker", "category", "result", "result_yes",
        "resolution_time", "resolution_time_trustworthy", "scheduled_end_time",
        "scheduled_lifetime_seconds", "can_close_early",
    ).sort("ticker")


def enrich_outcomes_with_metadata(outcomes: pl.DataFrame, metadata: pl.DataFrame) -> pl.DataFrame:
    """Fill missing resolution timestamps from the dedicated market backfill."""
    repaired = metadata.select(
        "ticker",
        pl.col("settled_time").cast(pl.String).str.to_datetime(time_zone="UTC", strict=False)
        .alias("metadata_resolution_time"),
    ).unique("ticker", keep="first")
    return outcomes.join(repaired, on="ticker", how="left").with_columns(
        pl.coalesce("resolution_time", "metadata_resolution_time").alias("resolution_time"),
        (pl.col("resolution_time_trustworthy") | pl.col("metadata_resolution_time").is_not_null())
        .alias("resolution_time_trustworthy"),
    ).drop("metadata_resolution_time").sort("ticker")


def build_market_relations(markets: pl.DataFrame) -> pl.DataFrame:
    return markets.with_columns(pl.col("volume").fill_null(0.0)).with_columns(
        pl.len().over("event_ticker").alias("event_group_size"),
        pl.col("volume").sum().over("event_ticker").alias("event_group_volume"),
        pl.col("ticker").rank("ordinal").over("event_ticker").cast(pl.Int64).alias("event_member_ordinal"),
        pl.lit("event_membership").alias("relation_type"),
        pl.lit("event-only; strike metadata unavailable in historical store").alias("relation_quality"),
    ).select(
        "ticker", "event_ticker", "series_ticker", "category", "relation_type",
        "relation_quality", "event_group_size", "event_group_volume", "event_member_ordinal",
    ).sort("event_ticker", "ticker")


def run() -> None:
    markets = pl.read_parquet(MARKETS / "*.parquet").filter(pl.col("result").is_in(["yes", "no"]))
    trades = pl.read_parquet(TRADES / "*.parquet")
    # Expand decision grids only for markets with tape. This reduces the
    # 2.7M-market catalog to the economically observable subset before the
    # twelve decision anchors are materialized.
    traded_markets = markets.join(trades.select("ticker").unique(), on="ticker", how="inner")
    points = build_decision_points(traded_markets, trades)
    outcomes = build_outcomes(markets)
    if MARKET_METADATA.exists() and any(MARKET_METADATA.glob("*.parquet")):
        outcomes = enrich_outcomes_with_metadata(
            outcomes, pl.read_parquet(MARKET_METADATA / "*.parquet")
        )
    relations = build_market_relations(markets)
    DECISION_POINTS.parent.mkdir(parents=True, exist_ok=True)
    points.write_parquet(DECISION_POINTS)
    outcomes.write_parquet(OUTCOMES)
    relations.write_parquet(MARKET_RELATIONS)
    print(f"decision points: {len(points):,} -> {DECISION_POINTS}")
    print(f"outcomes: {len(outcomes):,} -> {OUTCOMES}")
    print(f"relations: {len(relations):,} -> {MARKET_RELATIONS}")


if __name__ == "__main__":
    run()
