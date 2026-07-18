"""Common statistical gate for point-in-time external-data strategies."""

from __future__ import annotations

import math

import polars as pl

from .atlas import false_discovery_adjust
from .mechanism_suite import CARRY_APY
from .screens import cell_stats


def add_strategy_economics(
    frame: pl.DataFrame, spread_reserve_cents: int
) -> pl.DataFrame:
    """Price a selected YES/NO strategy as a conservative taker at last print."""
    yes_price = pl.col("yes_price_cents").cast(pl.Int64)
    selected_print = pl.when(pl.col("side") == "yes").then(yes_price).otherwise(
        100 - yes_price
    )
    entry = (selected_print + spread_reserve_cents).clip(1, 99)
    fee = ((7 * entry * (100 - entry) + 9999) // 10000).cast(pl.Int64)
    win = pl.when(pl.col("side") == "yes").then(
        pl.col("result_yes")
    ).otherwise(1 - pl.col("result_yes"))
    return frame.with_columns(
        entry.alias("entry_price_cents"), fee.alias("fee_cents")
    ).with_columns(
        ((100 * win - pl.col("entry_price_cents") - pl.col("fee_cents"))
         / pl.col("entry_price_cents")).alias("hold_return")
    ).with_columns(
        (
            pl.col("hold_return") * (365 * 86400) / pl.col("hold_seconds")
            + CARRY_APY
        ).alias("annualized_net_return")
    )


def _p_value(mean: float, se: float, hurdle: float) -> float:
    if not math.isfinite(mean) or not math.isfinite(se):
        return 1.0
    if se == 0:
        return 0.0 if mean > hurdle else 1.0
    return 0.5 * math.erfc(((mean - hurdle) / se) / math.sqrt(2))


def _search_correction(cells: pl.DataFrame, minimum_events: int) -> pl.DataFrame:
    cells = cells.with_columns(
        pl.when(
            (pl.col("n_periods") == 3)
            & (pl.col("minimum_fold_events") >= minimum_events)
        ).then(pl.col("worst_period_p")).otherwise(1.0).alias("search_p")
    )
    parts = []
    for _, family in cells.partition_by("family_id", as_dict=True).items():
        parts.append(
            family.with_columns(
                pl.Series("family_fdr_q", false_discovery_adjust(family["search_p"].to_list()))
            )
        )
    out = pl.concat(parts, how="vertical_relaxed").sort("family_id", "cell_id")
    return out.with_columns(
        pl.Series("suite_fdr_q", false_discovery_adjust(out["search_p"].to_list()))
    ).with_columns(
        (
            pl.col("passes_all_folds")
            & (pl.col("family_fdr_q") <= 0.05)
            & (pl.col("suite_fdr_q") <= 0.05)
        ).alias("historically_qualified")
    )


def evaluate_registered_cells(
    frame: pl.DataFrame,
    registered: pl.DataFrame,
    minimum_events: int,
    annual_hurdle: float,
    minimum_hold_return: float,
    z: float,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Evaluate every registered label, including labels with no observations."""
    required = {
        "family_id", "cell_id", "period", "event_ticker",
        "annualized_net_return", "hold_return", "incremental_return",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"external cell frame missing {', '.join(sorted(missing))}")
    folds = frame.filter(pl.col("period").is_in(["early", "middle", "recent"]))
    keys = ["family_id", "cell_id", "period"]
    annual = cell_stats(folds, keys, "annualized_net_return").rename({
        "annualized_net_return_mean": "mean_ann_net",
        "annualized_net_return_se": "annual_se",
    })
    hold = cell_stats(folds, keys, "hold_return").select(
        *keys,
        pl.col("hold_return_mean").alias("mean_hold_return"),
        pl.col("hold_return_se").alias("hold_se"),
    )
    incremental = cell_stats(folds, keys, "incremental_return").select(
        *keys,
        pl.col("incremental_return_mean").alias("mean_incremental"),
        pl.col("incremental_return_se").alias("incremental_se"),
    )
    periods = annual.join(hold, on=keys).join(incremental, on=keys).with_columns(
        (pl.col("mean_ann_net") - z * pl.col("annual_se")).alias("annual_lower_bound"),
        (pl.col("mean_hold_return") - z * pl.col("hold_se")).alias("hold_lower_bound"),
        (pl.col("mean_incremental") - z * pl.col("incremental_se")).alias(
            "incremental_lower_bound"
        ),
    ).with_columns(
        pl.struct("mean_ann_net", "annual_se").map_elements(
            lambda row: _p_value(row["mean_ann_net"], row["annual_se"], annual_hurdle),
            return_dtype=pl.Float64,
        ).alias("p_value"),
        (
            (pl.col("n_events") >= minimum_events)
            & (pl.col("annual_lower_bound") > annual_hurdle)
            & (pl.col("hold_lower_bound") > minimum_hold_return)
            & (pl.col("incremental_lower_bound") > 0)
        ).alias("period_pass"),
    )
    observed = periods.group_by("family_id", "cell_id").agg(
        pl.col("period").n_unique().alias("n_periods"),
        pl.col("period_pass").all().alias("all_observed_periods_pass"),
        pl.col("p_value").max().alias("worst_period_p"),
        pl.col("annual_lower_bound").min().alias("worst_annual_lower_bound"),
        pl.col("hold_lower_bound").min().alias("worst_hold_lower_bound"),
        pl.col("incremental_lower_bound").min().alias("worst_incremental_lower_bound"),
        pl.col("n_events").min().alias("minimum_fold_events"),
        pl.col("n").sum().alias("n_total"),
    ).with_columns(
        (
            (pl.col("n_periods") == 3) & pl.col("all_observed_periods_pass")
        ).alias("passes_all_folds")
    )
    cells = registered.unique(["family_id", "cell_id"]).join(
        observed, on=["family_id", "cell_id"], how="left"
    ).with_columns(
        pl.col("n_periods").fill_null(0),
        pl.col("all_observed_periods_pass").fill_null(False),
        pl.col("worst_period_p").fill_null(1.0),
        pl.col("minimum_fold_events").fill_null(0),
        pl.col("n_total").fill_null(0),
        pl.col("passes_all_folds").fill_null(False),
    )
    return periods.sort(*keys), _search_correction(cells, minimum_events)
