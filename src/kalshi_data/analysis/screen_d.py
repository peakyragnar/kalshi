"""Screen D: maker vs. taker economics from the trade tape.

Every trade record carries the aggressor side, so each fill yields two
observations at the same price: the taker's position and the maker's opposite
position. The realized settlement-return gap between them, by price bucket x
horizon, is the exchange's adverse-selection measure — and the maker-side rows
ARE the fill distribution a resting-order strategy would actually have gotten.

Fees vectorized: taker = ceil(7*p*(100-p)/10000) cents (integer arithmetic,
identical for both directions since p*(100-p) is symmetric); maker = 0 except
on quadratic_with_maker_fees series (25% of taker, ceil'd).
"""

from __future__ import annotations


import polars as pl

from .screens import cell_stats

from ..core.paths import MARKETS, TRADES, RESEARCH as REPORTS_DIR
DISCOVERY_END = "2025-07-01"



def trade_economics(trades: pl.DataFrame, markets: pl.DataFrame) -> pl.DataFrame:
    """One row per fill with maker/taker net hold returns and cell keys."""
    df = trades.join(markets, on="ticker", how="inner").filter(
        pl.col("result").is_in(["yes", "no"])
        & pl.col("yes_price_cents").is_between(1, 99)
    )
    p = pl.col("yes_price_cents")
    qn = 100 - p
    y = (pl.col("result") == "yes").cast(pl.Float64)
    fee_t = (7 * p * (100 - p) + 9999) // 10000
    fee_m = pl.when(pl.col("fee_type") == "quadratic_with_maker_fees").then(
        (7 * p * (100 - p) + 39999) // 40000
    ).otherwise(0)
    df = df.with_columns(
        ((pl.col("end_time") - pl.col("created_time")).dt.total_days()).alias("horizon_days"),
    ).filter(pl.col("horizon_days") >= 1)
    ret = lambda payoff, cost, fee: (payoff - cost - fee) / cost
    yes_pay, no_pay = 100 * y, 100 * (1 - y)
    df = df.with_columns(
        pl.when(pl.col("taker_side") == "yes")
        .then(ret(yes_pay, p, fee_t))
        .otherwise(ret(no_pay, qn, fee_t))
        .alias("ret_taker"),
        pl.when(pl.col("taker_side") == "yes")
        .then(ret(no_pay, qn, fee_m))
        .otherwise(ret(yes_pay, p, fee_m))
        .alias("ret_maker"),
    )
    hb = pl.col("horizon_days")
    hbucket = (
        pl.when(hb < 7).then(pl.lit("a 0-7d"))
        .when(hb < 30).then(pl.lit("b 7-30d"))
        .when(hb < 90).then(pl.lit("c 30-90d"))
        .when(hb < 180).then(pl.lit("d 90-180d"))
        .otherwise(pl.lit("e 180d+"))
    )
    pbucket = (
        pl.when(p < 5).then(pl.lit("01-5"))
        .when(p < 10).then(pl.lit("05-10"))
        .when(p < 20).then(pl.lit("10-20"))
        .when(p < 30).then(pl.lit("20-30"))
        .when(p < 40).then(pl.lit("30-40"))
        .when(p < 50).then(pl.lit("40-50"))
        .when(p < 60).then(pl.lit("50-60"))
        .when(p < 70).then(pl.lit("60-70"))
        .when(p < 80).then(pl.lit("70-80"))
        .when(p < 90).then(pl.lit("80-90"))
        .when(p < 95).then(pl.lit("90-95"))
        .otherwise(pl.lit("95-99"))
    )
    return df.with_columns(
        hbucket.alias("hbucket"),
        pbucket.alias("bucket"),
        (pl.col("ret_maker") - pl.col("ret_taker")).alias("gap"),
        pl.when(
            pl.col("end_time") < pl.lit(DISCOVERY_END).str.to_datetime(time_zone="UTC")
        ).then(pl.lit("discovery")).otherwise(pl.lit("confirmation")).alias("period"),
    )


def load() -> pl.DataFrame:
    markets = (
        pl.scan_parquet(MARKETS / "*.parquet")
        .select("ticker", "event_ticker", "category", "fee_type", "result",
                "close_time", "expiration_time")
        .with_columns(
            pl.col("close_time").str.to_datetime(time_zone="UTC", strict=False),
            pl.col("expiration_time").str.to_datetime(time_zone="UTC", strict=False),
        )
        .with_columns(pl.coalesce("close_time", "expiration_time").alias("end_time"))
        .select("ticker", "event_ticker", "category", "fee_type", "result", "end_time")
        .collect()
    )
    trades = (
        pl.scan_parquet(TRADES / "*.parquet")
        .select("ticker", "created_time", "yes_price_cents", "taker_side")
        .with_columns(pl.col("created_time").str.to_datetime(time_zone="UTC", strict=False))
        .collect()
    )
    return trade_economics(trades, markets)


def _md(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        out.append(
            "| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in row) + " |"
        )
    return out


def run() -> None:
    df = load()
    lines = ["# Screen D — maker vs. taker economics (realized, from fills)", ""]
    lines.append(f"Fills analyzed: **{len(df):,}** (deployment tape, settled markets, horizon >= 1d).")
    lines.append("")

    lines.append("## Maker-taker return gap per fill, by horizon (all buckets)")
    g = cell_stats(df, ["period", "hbucket"], "gap")
    m = cell_stats(df, ["period", "hbucket"], "ret_maker").select(
        "period", "hbucket", "ret_maker_mean", "ret_maker_se"
    )
    t = cell_stats(df, ["period", "hbucket"], "ret_taker").select(
        "period", "hbucket", "ret_taker_mean"
    )
    lines.extend(_md(g.join(m, on=["period", "hbucket"]).join(t, on=["period", "hbucket"])))
    lines.append("")

    lines.append("## Maker hold return by price bucket x horizon (confirmation)")
    conf = df.filter(pl.col("period") == "confirmation")
    lines.extend(_md(cell_stats(conf, ["hbucket", "bucket"], "ret_maker")))

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "screen_d.md").write_text("\n".join(lines))
    print(f"screen D written: reports/screen_d.md ({len(df):,} fills)")


if __name__ == "__main__":
    run()
