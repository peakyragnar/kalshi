"""Execution, capacity, and concentration audit for registered suite survivors."""

from __future__ import annotations

import math

import polars as pl

from .atlas import add_periods
from .mechanism_suite import CARRY_APY, _base_panel, build_path_rows
from .screens import cell_stats
from ..core.paths import MARKET_METADATA, RESEARCH, SURVIVOR_AUDIT, TRADES


CANDIDATE_ID = "T-1d->T-6h|-2:2|01-05|no"


def match_candidate_prints(path: pl.DataFrame, tape: pl.DataFrame) -> pl.DataFrame:
    """Match the exact print that supplied a candidate decision price."""
    return path.join(
        tape,
        on=["ticker", "trade_time", "yes_price_cents"],
        how="inner",
    )


def add_fill_execution_economics(frame: pl.DataFrame) -> pl.DataFrame:
    p = pl.col("yes_price_cents").cast(pl.Float64)
    q = 100 - p
    y = pl.col("result_yes").cast(pl.Float64)
    maker_fee = pl.when(pl.col("fee_type") == "quadratic_with_maker_fees").then(
        ((7 * p * (100 - p) + 39999) // 40000).cast(pl.Float64)
    ).otherwise(0.0)
    taker_fee = ((7 * p * (100 - p) + 9999) // 10000).cast(pl.Float64)
    out = frame.with_columns(
        pl.when(pl.col("taker_side") == "yes")
        .then(pl.lit("maker_no"))
        .otherwise(pl.lit("taker_no"))
        .alias("execution_role"),
        pl.when(pl.col("taker_side") == "yes").then(maker_fee).otherwise(taker_fee).alias("fee_cents"),
    ).with_columns(
        ((100 * (1 - y) - q - pl.col("fee_cents")) / q).alias("hold_return"),
        pl.col("count").alias("contracts"),
    )
    return out.with_columns(
        (pl.col("hold_return") * (365 * 86400) / pl.col("hold_seconds") + CARRY_APY)
        .alias("annualized_net_return")
    )


def _candidate_fills() -> pl.DataFrame:
    base = _base_panel()
    path = build_path_rows(base, [("T-1d", "T-6h")]).filter(
        pl.col("yes_price_cents").is_between(1, 5)
        & (pl.col("price_move_cents") >= -2)
        & (pl.col("price_move_cents") < 2)
    )
    metadata_parts = list(MARKET_METADATA.glob("*.parquet")) if MARKET_METADATA.exists() else []
    if metadata_parts:
        settled = pl.read_parquet(MARKET_METADATA / "*.parquet").unique("ticker", keep="first").select(
            "ticker",
            pl.col("settled_time").cast(pl.String).str.to_datetime(time_zone="UTC", strict=False),
        )
        path = path.join(settled, on="ticker", how="left")
    elif "settled_time" not in path.columns:
        path = path.with_columns(
            pl.lit(None).cast(pl.Datetime(time_zone="UTC")).alias("settled_time")
        )
    tape = pl.read_parquet(TRADES / "*.parquet").select(
        "ticker", "created_time", "taker_side", "count", "yes_price_cents", "is_block_trade"
    ).with_columns(
        pl.col("created_time").str.to_datetime(time_zone="UTC", strict=False).alias("trade_time")
    ).drop("created_time").filter(~pl.col("is_block_trade").fill_null(False))
    matched = add_periods(match_candidate_prints(path, tape)).with_columns(
        pl.when(pl.col("settled_time").is_not_null() & (pl.col("settled_time") > pl.col("trade_time")))
        .then((pl.col("settled_time") - pl.col("trade_time")).dt.total_seconds())
        .otherwise((pl.col("scheduled_end_time") - pl.col("trade_time")).dt.total_seconds())
        .alias("hold_seconds")
    ).filter(pl.col("hold_seconds") > 0)
    return add_fill_execution_economics(matched).with_columns(pl.lit(CANDIDATE_ID).alias("cell_id"))


def _fold_stats(fills: pl.DataFrame) -> pl.DataFrame:
    stats = cell_stats(fills, ["period", "execution_role"], "annualized_net_return").join(
        fills.group_by("period", "execution_role").agg(
            pl.col("hold_return").mean().alias("mean_hold_return"),
            (pl.col("hold_return") < 0).mean().alias("loss_rate"),
            pl.col("contracts").sum().alias("contracts"),
            pl.col("ticker").n_unique().alias("markets"),
        ),
        on=["period", "execution_role"], how="left",
    )
    return stats.with_columns(
        (pl.col("annualized_net_return_mean") - 2 * pl.col("annualized_net_return_se"))
        .alias("annualized_lower_bound")
    ).sort("execution_role", "period")


def _report(fills: pl.DataFrame, stats: pl.DataFrame) -> str:
    maker = fills.filter(pl.col("execution_role") == "maker_no")
    total_contracts = fills["contracts"].sum()
    maker_contracts = maker["contracts"].sum()
    event_capacity = maker.group_by("event_ticker").agg(pl.col("contracts").sum().alias("contracts"))
    max_event_share = (
        event_capacity["contracts"].max() / maker_contracts if maker_contracts and len(event_capacity) else math.nan
    )
    median_staleness_hours = fills["price_staleness_seconds"].median() / 3600
    p90_staleness_hours = fills["price_staleness_seconds"].quantile(0.9) / 3600
    category = maker.group_by("category").agg(
        pl.col("event_ticker").n_unique().alias("events"),
        pl.col("ticker").n_unique().alias("markets"),
        pl.col("contracts").sum().alias("contracts"),
        pl.col("hold_return").mean().alias("mean_hold_return"),
        (pl.col("hold_return") < 0).mean().alias("loss_rate"),
    ).sort("contracts", descending=True)
    category_fold = cell_stats(
        maker, ["category", "period"], "annualized_net_return"
    ).join(
        maker.group_by("category", "period").agg(
            pl.col("hold_return").mean().alias("mean_hold_return"),
            (pl.col("hold_return") < 0).mean().alias("loss_rate"),
            pl.col("contracts").sum().alias("contracts"),
        ),
        on=["category", "period"], how="left",
    ).with_columns(
        (pl.col("annualized_net_return_mean") - 2 * pl.col("annualized_net_return_se"))
        .alias("annualized_lower_bound")
    ).sort("category", "period")
    lines = [
        "# Survivor execution audit", "",
        f"Registered survivor: `{CANDIDATE_ID}`.", "",
        f"The candidate matched **{len(fills):,} recorded prints / {total_contracts:,.0f} contracts** "
        "by exact ticker, timestamp, and price. "
        f"Of those, **{len(maker):,} prints / {maker_contracts:,.0f} contracts** had a YES aggressor, "
        "which means the desired NO side was the historical maker fill.", "",
        "Recorded contract count is evidence of traded scale, not a claim that our counterfactual order "
        "would have received every contract. Historical top-of-book depth is unavailable.", "",
        f"The T-6h decision price was last printed a median **{median_staleness_hours:.2f} hours** "
        f"earlier (90th percentile **{p90_staleness_hours:.2f} hours**). Execution returns therefore "
        "start at the actual print timestamp, not the nominal T-6h decision time.", "",
        f"Largest event share of maker-side matched contracts: **{max_event_share:.2%}**.", "",
        "## Fold evidence by executable role", "",
        "| role | fold | fills | events | markets | contracts | mean hold | loss rate | ann. mean | ann. 2-SE lower |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in stats.iter_rows(named=True):
        lines.append(
            f"| {row['execution_role']} | {row['period']} | {row['n']:,} | {row['n_events']:,} | "
            f"{row['markets']:,} | {row['contracts']:,.0f} | {row['mean_hold_return']:.3%} | "
            f"{row['loss_rate']:.3%} | {row['annualized_net_return_mean']:.3f} | "
            f"{row['annualized_lower_bound']:.3f} |"
        )
    lines += ["", "## Maker-side category distribution", "", "| category | events | markets | contracts | mean hold | loss rate |", "|---|---:|---:|---:|---:|---:|"]
    for row in category.iter_rows(named=True):
        lines.append(
            f"| {row['category']} | {row['events']:,} | {row['markets']:,} | {row['contracts']:,.0f} | "
            f"{row['mean_hold_return']:.3%} | {row['loss_rate']:.3%} |"
        )
    lines += [
        "", "## Maker-side category stability by fold", "",
        "This breakdown is diagnostic and post-selection; it does not create separately qualified category cells.", "",
        "| category | fold | fills | events | contracts | mean hold | loss rate | ann. 2-SE lower |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in category_fold.iter_rows(named=True):
        lines.append(
            f"| {row['category']} | {row['period']} | {row['n']:,} | {row['n_events']:,} | "
            f"{row['contracts']:,.0f} | {row['mean_hold_return']:.3%} | {row['loss_rate']:.3%} | "
            f"{row['annualized_lower_bound']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def run() -> None:
    fills = _candidate_fills()
    stats = _fold_stats(fills)
    SURVIVOR_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    fills.write_parquet(SURVIVOR_AUDIT)
    (RESEARCH / "survivor-audit.md").write_text(_report(fills, stats))
    print(f"survivor audit: {len(fills):,} matched prints -> {SURVIVOR_AUDIT}", flush=True)


if __name__ == "__main__":
    run()
