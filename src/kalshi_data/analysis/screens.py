"""Screen machinery: fees, price buckets, cluster-robust errors, calibration cells.

All conventions from phase0-assumptions.md:
- taker fee ceil'd to the cent per fill; maker fee zero except
  quadratic_with_maker_fees series (25% of taker, ceil'd)
- maker entry = snapshot price + provisional 2c haircut (until Screen D)
- staleness filter: snapshot trade at most 20% of the horizon old
- SEs clustered by event
- discovery = resolved before 2025-07-01; confirmation = after
"""

from __future__ import annotations

import math

import polars as pl

BUCKET_EDGES = [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
DISCOVERY_END = "2025-07-01"
MAKER_HAIRCUT_CENTS = 2
STALENESS_FRACTION = 0.20
MIN_TRADES = 25


def taker_fee_cents(p: int) -> int:
    return math.ceil(7 * p * (100 - p) / 10000)


def maker_fee_cents(p: int, fee_type: str) -> int:
    if fee_type == "quadratic_with_maker_fees":
        return math.ceil(1.75 * p * (100 - p) / 10000)
    return 0


def bucket_label(p: int) -> str:
    for lo, hi in zip(BUCKET_EDGES, BUCKET_EDGES[1:]):
        if lo <= p < hi or (hi == 100 and p == 99):
            return f"{lo:02d}-{hi if hi < 100 else 99}"
    return "out"


def cluster_se(values: pl.Series, clusters: pl.Series) -> float:
    """Cluster-robust (CR0) standard error of the mean."""
    df = pl.DataFrame({"x": values, "c": clusters})
    n = len(df)
    if n == 0:
        return float("nan")
    mean = df["x"].mean()
    resid_sums = df.group_by("c").agg((pl.col("x") - mean).sum().alias("e"))["e"]
    return math.sqrt(float((resid_sums**2).sum())) / n


def prepare(snapshots: pl.DataFrame, trade_counts: pl.DataFrame) -> pl.DataFrame:
    """Apply pre-committed filters and add derived columns for all screens."""
    df = snapshots.join(trade_counts, on="ticker", how="left")
    df = df.filter(
        (pl.col("n_trades") >= MIN_TRADES)
        & (pl.col("yes_price_cents") >= 1)
        & (pl.col("yes_price_cents") <= 99)
        & (pl.col("staleness_s") <= pl.col("horizon_days") * 86400 * STALENESS_FRACTION)
        & (pl.col("hold_days") >= 1)
    )
    p = pl.col("yes_price_cents")
    fee_taker = p.map_elements(taker_fee_cents, return_dtype=pl.Int64)
    fee_maker = pl.struct(["yes_price_cents", "fee_type"]).map_elements(
        lambda s: maker_fee_cents(s["yes_price_cents"], s["fee_type"] or ""),
        return_dtype=pl.Int64,
    )
    p_maker = (p + MAKER_HAIRCUT_CENTS).clip(upper_bound=99)
    y = pl.col("result_yes").cast(pl.Float64)
    return df.with_columns(
        p.map_elements(bucket_label, return_dtype=pl.String).alias("bucket"),
        ((100 * y - p - fee_taker) / p).alias("ret_taker"),
        ((100 * y - p_maker - fee_maker) / p_maker).alias("ret_maker"),
        (
            (pl.col("snap_ts") + pl.duration(days=pl.col("hold_days")))
            < pl.lit(DISCOVERY_END).str.to_datetime(time_zone="UTC")
        )
        .replace_strict({True: "discovery", False: "confirmation"})
        .alias("period"),
    ).with_columns(
        (pl.col("ret_taker") * 365 / pl.col("hold_days")).alias("ann_taker"),
        (pl.col("ret_maker") * 365 / pl.col("hold_days")).alias("ann_maker"),
    )


def cell_stats(df: pl.DataFrame, cell_cols: list[str], value: str) -> pl.DataFrame:
    """Vectorized per-cell mean with CR0 event-clustered SE (for large frames)."""
    g = df.group_by(cell_cols + ["event_ticker"]).agg(
        pl.len().alias("nc"), pl.col(value).sum().alias("sc")
    )
    agg = g.group_by(cell_cols).agg(
        pl.col("nc").sum().alias("n"),
        pl.col("sc").sum().alias("s"),
        pl.len().alias("n_events"),
    )
    e = g.join(agg, on=cell_cols).with_columns(
        (pl.col("sc") - pl.col("nc") * (pl.col("s") / pl.col("n"))).alias("e")
    )
    se = e.group_by(cell_cols).agg(
        ((pl.col("e") ** 2).sum().sqrt() / pl.col("n").first()).alias(f"{value}_se")
    )
    return (
        agg.with_columns((pl.col("s") / pl.col("n")).alias(f"{value}_mean"))
        .drop("s")
        .join(se, on=cell_cols)
        .sort(cell_cols)
    )


def cells(df: pl.DataFrame, group_cols: list[str]) -> pl.DataFrame:
    """Aggregate calibration + return stats per cell with clustered SEs."""
    rows = []
    for key, cell in df.group_by(group_cols, maintain_order=True):
        rec = dict(zip(group_cols, key))
        rec["n"] = len(cell)
        rec["n_events"] = cell["event_ticker"].n_unique()
        rec["implied"] = round(float(cell["yes_price_cents"].mean()) / 100, 4)
        rec["realized"] = round(float(cell["result_yes"].mean()), 4)
        for side in ("taker", "maker"):
            rec[f"hold_ret_{side}"] = round(float(cell[f"ret_{side}"].mean()), 4)
            rec[f"ann_{side}"] = round(float(cell[f"ann_{side}"].mean()), 4)
            rec[f"ann_{side}_se"] = round(
                cluster_se(cell[f"ann_{side}"], cell["event_ticker"]), 4
            )
        rows.append(rec)
    return pl.DataFrame(rows).sort(group_cols)
