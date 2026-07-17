"""Flow-shock overshoot screen, pre-committed in research/flow-shock-precommit.md.

Tests whether concentrated aggressive YES bursts in 1-19c longshots predict
subsequent price reversion and improve NO-side settlement economics relative to
ordinary snapshots in the same category, price bucket and horizon.
"""

from __future__ import annotations

import math

import polars as pl

from .screen_b import CARRY_APY, no_returns
from .screens import DISCOVERY_END, cell_stats, cluster_se, prepare
from ..core.paths import DERIVED, MARKETS, RESEARCH, TRADES

BAR_HOURS = 1
PRIOR_ACTIVE_BARS = 20
MIN_PRIOR_BARS = 10
MIN_YES_VOLUME = 250.0
MIN_VOLUME_MULTIPLE = 10.0
MIN_YES_SHARE = 0.80
MIN_PRICE_JUMP_CENTS = 2
MAX_PREVIOUS_BAR_GAP_HOURS = 24
MIN_DAYS_LEFT = 7
MAX_DAYS_LEFT = 180
MIN_PRICE_CENTS = 1
MAX_PRICE_EXCLUSIVE = 20
MIN_BASELINE_N = 50
HURDLE = 0.07
MIN_SIGNALS = 100
MIN_EVENTS = 50
FORWARD_HOURS = (24, 168)


def _hourly_bars_lazy(trades: pl.LazyFrame, markets: pl.LazyFrame) -> pl.LazyFrame:
    tape = (
        trades.filter(~pl.col("is_block_trade").fill_null(False))
        .join(markets, on="ticker", how="inner")
        .with_columns(
            ((pl.col("end_time") - pl.col("created_time")).dt.total_seconds() / 86400).alias(
                "days_left"
            )
        )
        .filter(
            pl.col("yes_price_cents").is_between(
                MIN_PRICE_CENTS, MAX_PRICE_EXCLUSIVE, closed="left"
            ),
            pl.col("days_left").is_between(MIN_DAYS_LEFT, MAX_DAYS_LEFT),
        )
        .sort("ticker", "created_time", "trade_id")
        .with_columns(
            pl.col("created_time").dt.truncate(f"{BAR_HOURS}h").alias("hour"),
            pl.when(pl.col("taker_side") == "yes")
            .then(pl.col("created_time"))
            .alias("_yes_time"),
            pl.when(pl.col("taker_side") == "yes").then(pl.col("trade_id")).alias("_yes_id"),
            pl.when(pl.col("taker_side") == "yes")
            .then(pl.col("yes_price_cents"))
            .alias("_yes_price"),
        )
    )
    bars = (
        tape.group_by("ticker", "hour", maintain_order=True)
        .agg(
            pl.col("event_ticker").first(),
            pl.col("category").first(),
            pl.col("fee_type").first(),
            pl.col("result").first(),
            pl.col("end_time").first(),
            pl.col("count").sum().alias("total_volume"),
            pl.col("count").filter(pl.col("taker_side") == "yes").sum().alias("yes_volume"),
            pl.col("yes_price_cents")
            .sort_by("created_time", "trade_id")
            .last()
            .alias("close_price"),
            pl.col("_yes_price").sort_by("_yes_time", "_yes_id").last().alias("yes_close"),
        )
        .sort("ticker", "hour")
        .with_columns(
            pl.col("yes_volume")
            .shift(1)
            .rolling_median(window_size=PRIOR_ACTIVE_BARS, min_samples=MIN_PRIOR_BARS)
            .over("ticker")
            .alias("prior_yes_median"),
            pl.col("close_price").shift(1).over("ticker").alias("previous_close"),
            pl.col("hour").shift(1).over("ticker").alias("previous_hour"),
        )
        .with_columns(
            (pl.col("yes_volume") / pl.col("total_volume")).alias("yes_share"),
            (pl.col("yes_close") - pl.col("previous_close")).alias("price_jump"),
            (
                (pl.col("hour") - pl.col("previous_hour")).dt.total_seconds() / 3600
            ).alias("previous_gap_hours"),
        )
    )
    return bars


def build_hourly_bars(trades: pl.DataFrame, markets: pl.DataFrame) -> pl.DataFrame:
    """Pure/eager wrapper used by deterministic unit tests."""
    return _hourly_bars_lazy(trades.lazy(), markets.lazy()).collect()


def _bucket_expr(price: pl.Expr) -> pl.Expr:
    return (
        pl.when(price < 5)
        .then(pl.lit("01-5"))
        .when(price < 10)
        .then(pl.lit("05-10"))
        .otherwise(pl.lit("10-20"))
    )


def _horizon_expr(days: pl.Expr) -> pl.Expr:
    return (
        pl.when(days < 18)
        .then(pl.lit(7))
        .when(days < 60)
        .then(pl.lit(30))
        .when(days < 135)
        .then(pl.lit(90))
        .otherwise(pl.lit(180))
    )


def select_shocks(bars: pl.DataFrame) -> pl.DataFrame:
    """Apply the fixed signal and derive settlement economics."""
    shocks = (
        bars.filter(
            pl.col("prior_yes_median").is_not_null(),
            pl.col("prior_yes_median") > 0,
            pl.col("yes_volume") >= MIN_YES_VOLUME,
            pl.col("yes_volume") >= MIN_VOLUME_MULTIPLE * pl.col("prior_yes_median"),
            pl.col("yes_share") >= MIN_YES_SHARE,
            pl.col("price_jump") >= MIN_PRICE_JUMP_CENTS,
            pl.col("previous_gap_hours") <= MAX_PREVIOUS_BAR_GAP_HOURS,
        )
        .sort("ticker", "hour")
        .unique(subset="ticker", keep="first", maintain_order=True)
        .with_columns(
            (pl.col("hour") + pl.duration(hours=BAR_HOURS)).alias("signal_ts"),
            pl.col("yes_close").alias("shock_price"),
            (pl.col("yes_volume") / pl.col("prior_yes_median")).alias("volume_multiple"),
        )
        .with_columns(
            ((pl.col("end_time") - pl.col("signal_ts")).dt.total_seconds() / 86400).alias(
                "hold_days"
            ),
            (pl.col("result") == "yes").cast(pl.Int8).alias("result_yes"),
        )
        .filter(pl.col("hold_days") >= 1)
    )
    p = pl.col("shock_price")
    q = 100 - p
    fee = pl.when(pl.col("fee_type") == "quadratic_with_maker_fees").then(
        (7 * p * (100 - p) + 39999) // 40000
    ).otherwise(0)
    y = pl.col("result_yes").cast(pl.Float64)
    ret = (100 * (1 - y) - q - fee) / q
    return shocks.with_columns(
        _bucket_expr(p).alias("bucket"),
        _horizon_expr(pl.col("hold_days")).alias("horizon_days"),
        pl.when(
            pl.col("end_time") < pl.lit(DISCOVERY_END).str.to_datetime(time_zone="UTC")
        )
        .then(pl.lit("discovery"))
        .otherwise(pl.lit("confirmation"))
        .alias("period"),
        ret.alias("ret_no"),
        ((ret + CARRY_APY * pl.col("hold_days") / 365) * 365 / pl.col("hold_days")).alias(
            "ann_no_carry"
        ),
        (y - p / 100).alias("calibration_error"),
    )


def attach_forward_changes(
    shocks: pl.DataFrame, tape: pl.DataFrame, horizons_hours: tuple[int, ...] = FORWARD_HOURS
) -> pl.DataFrame:
    """Latest post-signal price by each horizon, plus conservative zero imputation."""
    out = shocks
    right = tape.sort("created_time", "trade_id").select(
        "ticker", "created_time", "yes_price_cents"
    )
    for hours in horizons_hours:
        target = f"_target_{hours}h"
        trade_ts = f"_trade_{hours}h"
        forward_price = f"_price_{hours}h"
        out = out.with_columns(
            (pl.col("signal_ts") + pl.duration(hours=hours)).alias(target)
        ).sort(target)
        matched = out.join_asof(
            right.rename({"created_time": trade_ts, "yes_price_cents": forward_price}),
            left_on=target,
            right_on=trade_ts,
            by="ticker",
            strategy="backward",
        )
        valid = pl.col(trade_ts).is_not_null() & (pl.col(trade_ts) > pl.col("signal_ts"))
        change = pl.when(valid).then(pl.col(forward_price) - pl.col("shock_price"))
        out = matched.with_columns(
            valid.alias(f"has_followup_{hours}h"),
            change.alias(f"change_{hours}h"),
            change.fill_null(0).alias(f"change_{hours}h_zero"),
        ).drop(target, trade_ts, forward_price)
    return out.sort("ticker")


def gate_verdict(stats: dict[str, dict]) -> tuple[str, list[str]]:
    failures: list[str] = []
    for period in ("discovery", "confirmation"):
        s = stats.get(period, {})
        if s.get("n", 0) < MIN_SIGNALS or s.get("events", 0) < MIN_EVENTS:
            failures.append(f"{period} support below {MIN_SIGNALS} signals/{MIN_EVENTS} events")
            continue
        if s["change_168h_zero_mean"] + 2 * s["change_168h_zero_se"] >= 0:
            failures.append(f"{period} seven-day reversion does not clear 2SE")
        if s["ann_no_carry_mean"] - 2 * s["ann_no_carry_se"] <= HURDLE:
            failures.append(f"{period} absolute NO return does not clear 7% at 2SE")
        if s["uplift_mean"] - 2 * s["uplift_se"] <= 0:
            failures.append(f"{period} uplift does not clear zero at 2SE")
    return ("GREEN" if not failures else "RED"), failures


def _market_scan() -> pl.LazyFrame:
    return (
        pl.scan_parquet(MARKETS / "*.parquet")
        .filter((pl.col("tier") == "deployment") & pl.col("result").is_in(["yes", "no"]))
        .select(
            "ticker",
            "event_ticker",
            "category",
            "fee_type",
            "result",
            "close_time",
            "expiration_time",
        )
        .with_columns(
            pl.col("close_time").str.to_datetime(time_zone="UTC", strict=False),
            pl.col("expiration_time").str.to_datetime(time_zone="UTC", strict=False),
        )
        .with_columns(pl.coalesce("close_time", "expiration_time").alias("end_time"))
        .select("ticker", "event_ticker", "category", "fee_type", "result", "end_time")
    )


def _trade_scan() -> pl.LazyFrame:
    return (
        pl.scan_parquet(TRADES / "*.parquet")
        .select(
            "ticker",
            "trade_id",
            "created_time",
            "yes_price_cents",
            "count",
            "taker_side",
            "is_block_trade",
        )
        .with_columns(pl.col("created_time").str.to_datetime(time_zone="UTC", strict=False))
    )


def _baseline_cells(shocks: pl.DataFrame) -> pl.DataFrame:
    snapshots = pl.read_parquet(DERIVED / "snapshots.parquet")
    trade_counts = (
        pl.scan_parquet(TRADES / "*.parquet")
        .group_by("ticker")
        .agg(pl.len().alias("n_trades"))
        .collect()
    )
    controls = no_returns(prepare(snapshots, trade_counts)).filter(
        pl.col("horizon_days").is_in([7, 30, 90, 180]),
        pl.col("yes_price_cents").is_between(
            MIN_PRICE_CENTS, MAX_PRICE_EXCLUSIVE, closed="left"
        ),
        ~pl.col("ticker").is_in(shocks["ticker"].implode()),
    )
    keys = ["period", "category", "horizon_days", "bucket"]
    return cell_stats(controls, keys, "ann_no_carry").filter(pl.col("n") >= MIN_BASELINE_N)


def _summary(frame: pl.DataFrame) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for period in ("discovery", "confirmation"):
        sub = frame.filter(pl.col("period") == period).drop_nulls("uplift")
        rec: dict = {"n": len(sub), "events": sub["event_ticker"].n_unique()}
        for value in (
            "change_24h_zero",
            "change_168h_zero",
            "ann_no_carry",
            "calibration_error",
            "uplift",
        ):
            rec[f"{value}_mean"] = float(sub[value].mean())
            rec[f"{value}_se"] = cluster_se(sub[value], sub["event_ticker"])
        cell_weights = (
            sub.group_by("category", "horizon_days", "bucket")
            .agg(pl.len().alias("cell_n"), pl.col("baseline_se").first().alias("base_se"))
            .with_columns((pl.col("cell_n") / len(sub)).alias("w"))
        )
        baseline_uncertainty = math.sqrt(
            float(((cell_weights["w"] * cell_weights["base_se"]) ** 2).sum())
        )
        rec["uplift_se_shock"] = rec["uplift_se"]
        rec["baseline_uncertainty"] = baseline_uncertainty
        rec["uplift_se"] = math.sqrt(rec["uplift_se"] ** 2 + baseline_uncertainty**2)
        for hours in FORWARD_HOURS:
            rec[f"followup_{hours}h"] = float(sub[f"has_followup_{hours}h"].mean())
        out[period] = rec
    return out


def _category_table(frame: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for (period, category), sub in frame.drop_nulls("uplift").group_by(
        "period", "category", maintain_order=True
    ):
        events = sub["event_ticker"].n_unique()
        if events < 20:
            continue
        rows.append(
            {
                "period": period,
                "category": category,
                "n": len(sub),
                "events": events,
                "shock_price": round(float(sub["shock_price"].mean()), 2),
                "change_7d": round(float(sub["change_168h_zero"].mean()), 3),
                "ann_no": round(float(sub["ann_no_carry"].mean()), 3),
                "uplift": round(float(sub["uplift"].mean()), 3),
                "tail_rate": round(float(sub["result_yes"].mean()), 4),
            }
        )
    return pl.DataFrame(rows).sort("period", "n", descending=[False, True]) if rows else pl.DataFrame()


def _md(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        lines.append(
            "| "
            + " | ".join(
                f"{v:.4f}" if isinstance(v, float) else ("" if v is None else str(v)) for v in row
            )
            + " |"
        )
    return lines


def run() -> tuple[str, dict]:
    bars = _hourly_bars_lazy(_trade_scan(), _market_scan()).collect(engine="streaming")
    shocks = select_shocks(bars)
    tickers = shocks["ticker"].to_list()
    tape = (
        _trade_scan()
        .filter(pl.col("ticker").is_in(tickers), ~pl.col("is_block_trade").fill_null(False))
        .select("ticker", "trade_id", "created_time", "yes_price_cents")
        .collect(engine="streaming")
    )
    shocks = attach_forward_changes(shocks, tape)
    baselines = _baseline_cells(shocks).rename(
        {"ann_no_carry_mean": "baseline_mean", "ann_no_carry_se": "baseline_se"}
    )
    keys = ["period", "category", "horizon_days", "bucket"]
    frame = shocks.join(
        baselines.select(keys + ["baseline_mean", "baseline_se"]), on=keys, how="left"
    ).with_columns((pl.col("ann_no_carry") - pl.col("baseline_mean")).alias("uplift"))
    stats = _summary(frame)
    verdict, failures = gate_verdict(stats)

    DERIVED.mkdir(exist_ok=True)
    frame.write_parquet(DERIVED / "flow_shocks.parquet")

    lines = [f"# Flow-shock overshoot — {verdict}", ""]
    lines.append(
        "Pre-committed definition: `research/flow-shock-precommit.md`. "
        "This screen excludes sports, crypto instrumentation, parlays and block trades."
    )
    lines.append("")
    lines.append(f"Signals found: **{len(shocks):,}** across {shocks['event_ticker'].n_unique():,} events.")
    lines.append("")
    lines.append("## Support and matching")
    support_rows = []
    distribution_rows = []
    for period in ("discovery", "confirmation"):
        raw = frame.filter(pl.col("period") == period)
        matched = raw.drop_nulls("baseline_mean")
        event_counts = matched.group_by("event_ticker").len().sort("len", descending=True)
        support_rows.append(
            {
                "period": period,
                "signals": len(raw),
                "matched": len(matched),
                "events": matched["event_ticker"].n_unique(),
                "follow_7d": float(matched["has_followup_168h"].mean()),
                "top10_event_share": float(event_counts.head(10)["len"].sum() / len(matched)),
            }
        )
        distribution_rows.append(
            {
                "period": period,
                "mean_7d": float(matched["change_168h_zero"].mean()),
                "median_7d": float(matched["change_168h_zero"].median()),
                "p10": float(matched["change_168h_zero"].quantile(0.10)),
                "p90": float(matched["change_168h_zero"].quantile(0.90)),
                "share_down": float((matched["change_168h_zero"] < 0).mean()),
            }
        )
    lines.extend(_md(pl.DataFrame(support_rows)))
    lines.append("")
    lines.append("## Gate results")
    rows = []
    for period, s in stats.items():
        rows.append(
            {
                "period": period,
                "n": s["n"],
                "events": s["events"],
                "7d_change": s["change_168h_zero_mean"],
                "7d_se": s["change_168h_zero_se"],
                "ann_no": s["ann_no_carry_mean"],
                "ann_se": s["ann_no_carry_se"],
                "uplift": s["uplift_mean"],
                "uplift_se": s["uplift_se"],
                "follow_7d": s["followup_168h"],
            }
        )
    lines.extend(_md(pl.DataFrame(rows)))
    lines.append("")
    if failures:
        lines.append("### Failed conditions")
        lines.extend(f"- {f}" for f in failures)
    else:
        lines.append("All four gates clear in both periods.")
    lines.append("")
    lines.append("## Distribution check")
    lines.extend(_md(pl.DataFrame(distribution_rows)))
    lines.append("")
    medians = {r["period"]: r["median_7d"] for r in distribution_rows}
    lines.append(
        f"Median seven-day changes are {medians['discovery']:+.1f}¢ in discovery and "
        f"{medians['confirmation']:+.1f}¢ in confirmation. The gate uses event-clustered "
        "means rather than win rate or median because rare continuations can dominate "
        "settlement economics."
    )
    lines.append("")
    lines.append("## Exploratory category breakdown (not a qualification gate)")
    category = _category_table(frame)
    lines.extend(_md(category) if len(category) else ["*(no category has 20 event clusters)*"])
    lines.append("")
    lines.append(
        "Category rows are exploratory only. None is promoted without a separately "
        "registered cross-period category gate."
    )
    lines.append("")
    lines.append(
        "Settlement returns are conditional economics at the shock-hour anchor, not a "
        "claim that a newly placed resting order would have filled. No deployment rule changes automatically."
    )
    RESEARCH.mkdir(exist_ok=True)
    (RESEARCH / "flow_shock.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return verdict, stats


if __name__ == "__main__":
    run()
