"""Screen B: the term premium test.

Does the annualized NO-side edge rise with lockup duration once composition is
controlled? Three estimates, weakest to strongest identification:

1. raw        - ann return by horizon (confounded by what trades at each horizon)
2. controlled - residualized on category x price-bucket cells that span >= 2
                horizons (composition effect removed)
3. within     - residualized on the market itself, for markets observed at >= 2
                horizons (same market, different distance to settlement)

Plus the Aug-2025 natural experiment: positions initiated before Kalshi paid
interest on open positions sacrificed the full yield to hold; if the discount
is lockup compensation, it should compress after 2025-08-01.

NO-side maker economics per Screen D's validation: zero maker fee except the
designated series; entry at snapshot price (constant convention across
horizons, so slopes are unaffected).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from .screens import cell_stats, prepare

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
CARRY_APY = 0.0325
INTEREST_LAUNCH = "2025-08-01"


def no_returns(df: pl.DataFrame) -> pl.DataFrame:
    p = pl.col("yes_price_cents")
    q = 100 - p
    y = pl.col("result_yes").cast(pl.Float64)
    fee_m = pl.when(pl.col("fee_type") == "quadratic_with_maker_fees").then(
        (7 * p * (100 - p) + 39999) // 40000
    ).otherwise(0)
    return df.with_columns(
        ((100 * (1 - y) - q - fee_m) / q).alias("ret_no")
    ).with_columns(
        (pl.col("ret_no") * 365 / pl.col("hold_days")).alias("ann_no"),
        ((pl.col("ret_no") + CARRY_APY * pl.col("hold_days") / 365) * 365 / pl.col("hold_days")).alias(
            "ann_no_carry"
        ),
        pl.when(pl.col("snap_ts") >= pl.lit(INTEREST_LAUNCH).str.to_datetime(time_zone="UTC"))
        .then(pl.lit("post-interest"))
        .otherwise(pl.lit("pre-interest"))
        .alias("carry_regime"),
    )


def residualize(df: pl.DataFrame, group_cols: list[str], value: str = "ann_no") -> pl.DataFrame:
    """Demean `value` within groups, keeping only groups spanning >= 2 horizons."""
    spans = df.group_by(group_cols).agg(pl.col("horizon_days").n_unique().alias("nh"))
    keep = spans.filter(pl.col("nh") >= 2).drop("nh")
    sub = df.join(keep, on=group_cols, how="inner")
    return sub.with_columns(
        (pl.col(value) - pl.col(value).mean().over(group_cols)).alias("resid")
    )


def _md(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        out.append(
            "| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in row) + " |"
        )
    return out


def run() -> None:
    snapshots = pl.read_parquet(DATA_DIR / "derived" / "snapshots.parquet")
    trade_counts = (
        pl.scan_parquet(DATA_DIR / "trades" / "*.parquet")
        .group_by("ticker")
        .agg(pl.len().alias("n_trades"))
        .collect()
    )
    df = no_returns(prepare(snapshots, trade_counts))

    lines = ["# Screen B — term premium (lockup) test", ""]
    lines.append(f"Snapshots analyzed: **{len(df):,}**. NO-side maker economics, carry {CARRY_APY:.2%}.")
    lines.append("")

    lines.append("## Identification: support by category x horizon (n snapshots)")
    support = (
        df.group_by(["category", "horizon_days"]).len()
        .pivot(values="len", index="category", on="horizon_days")
        .sort("category")
    )
    lines.extend(_md(support))
    lines.append("")

    lines.append("## 1. Raw annualized NO return by horizon (confounded)")
    raw = cell_stats(df, ["horizon_days"], "ann_no").with_columns(
        (pl.col("ann_no_mean") + CARRY_APY).alias("with_carry")
    )
    lines.extend(_md(raw))
    lines.append("")

    lines.append("## 2. Controlled: residualized within category x bucket (slope only)")
    ctrl = residualize(df, ["category", "bucket"])
    lines.extend(_md(cell_stats(ctrl, ["horizon_days"], "resid")))
    lines.append("")

    lines.append("## 3. Within-market: residualized within ticker (strongest)")
    within = residualize(df, ["ticker"])
    lines.extend(_md(cell_stats(within, ["horizon_days"], "resid")))
    lines.append("")

    lines.append("## 4. Carry natural experiment (controlled slope, by regime)")
    for regime in ("pre-interest", "post-interest"):
        sub = residualize(df.filter(pl.col("carry_regime") == regime), ["category", "bucket"])
        lines.append(f"### {regime}")
        lines.extend(_md(cell_stats(sub, ["horizon_days"], "resid")))
        lines.append("")
    lines.append("### Overall NO edge by regime (raw, >=30d horizons)")
    lines.extend(
        _md(cell_stats(df.filter(pl.col("horizon_days") >= 30), ["carry_regime"], "ann_no"))
    )

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "screen_b.md").write_text("\n".join(lines))
    print(f"screen B written: reports/screen_b.md ({len(df):,} snapshots)")


if __name__ == "__main__":
    run()
