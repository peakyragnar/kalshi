"""Weekly edge health: recompute the qualifying cells on trailing windows and
grade them against the pre-committed traffic lights (edge-program-plan.md T1).

Lights (fixed before any drift was observed):
  GREEN - trailing-90d edge - 1*SE >= 7% hurdle
  AMBER - trailing-90d edge - 1*SE <  7%      -> halve new-entry size
  RED   - trailing-90d edge - 1*SE <  3.25%   -> stop new entries
  THIN  - fewer than 30 resolved snapshots in the window (no verdict, say so)

Also tracks the falsification metrics: trailing calibration gap (F1) and
trailing maker-taker gap (F4). Appends one history row per run to
data/edge_health_history.jsonl for the dashboard time series.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl

from .screen_b import no_returns
from .screen_d import load as load_fills
from .screens import cell_stats, prepare

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
HISTORY = DATA_DIR / "edge_health_history.jsonl"

HURDLE = 0.07
CARRY = 0.0325
MIN_N = 30

TICKET = ["KXRTICKET", "KXDTICKET", "KXWCPRICE", "KXNHLPRICE", "KXNBAFINALSPRICE"]

CELLS = {
    "politics_30d": dict(category="Politics", horizon=30, p_lo=1, p_hi=4, baseline=0.287),
    "financials_90d": dict(category="Financials", horizon=90, p_lo=1, p_hi=9, baseline=0.168),
}


def light(mean: float | None, se: float | None, n: int) -> str:
    if mean is None or se is None or n < MIN_N:
        return "THIN"
    bound = mean - se
    if bound < CARRY:
        return "RED"
    if bound < HURDLE:
        return "AMBER"
    return "GREEN"


def cell_frame(df: pl.DataFrame, spec: dict) -> pl.DataFrame:
    sub = df.filter(
        (pl.col("category") == spec["category"])
        & (pl.col("horizon_days") == spec["horizon"])
        & (pl.col("yes_price_cents").is_between(spec["p_lo"], spec["p_hi"]))
    )
    if spec["category"] == "Financials":
        sub = sub.filter(~pl.col("series_ticker").is_in(TICKET))
    return sub


def run() -> dict:
    now = dt.datetime.now(dt.timezone.utc)
    snapshots = pl.read_parquet(DATA_DIR / "derived" / "snapshots.parquet")
    trade_counts = (
        pl.scan_parquet(DATA_DIR / "trades" / "*.parquet")
        .group_by("ticker").agg(pl.len().alias("n_trades")).collect()
    )
    df = no_returns(prepare(snapshots, trade_counts)).with_columns(
        (pl.col("snap_ts") + pl.duration(days=pl.col("hold_days"))).alias("resolve_ts")
    )

    record: dict = {"ts": now.isoformat(timespec="seconds"), "cells": {}}
    for name, spec in CELLS.items():
        cell = cell_frame(df, spec)
        entry: dict = {"baseline": spec["baseline"]}
        for window in (90, 365):
            sub = cell.filter(pl.col("resolve_ts") >= now - dt.timedelta(days=window))
            if len(sub) == 0:
                entry[f"t{window}"] = {"n": 0, "mean": None, "se": None}
                continue
            s = cell_stats(sub.with_columns(pl.lit("x").alias("k")), ["k"], "ann_no_carry").row(0, named=True)
            entry[f"t{window}"] = {
                "n": s["n"], "events": s["n_events"],
                "mean": round(s["ann_no_carry_mean"], 4),
                "se": round(s["ann_no_carry_se"], 4),
            }
        t90 = entry["t90"]
        entry["light"] = light(t90.get("mean"), t90.get("se"), t90.get("n", 0))
        record["cells"][name] = entry

    long = df.filter(pl.col("horizon_days") >= 30).filter(
        pl.col("resolve_ts") >= now - dt.timedelta(days=90)
    )
    record["calibration_gap_t90"] = (
        round(float((long["result_yes"].cast(pl.Float64) - long["yes_price_cents"] / 100).mean()), 4)
        if len(long) else None
    )
    fills = load_fills().filter(
        (pl.col("end_time") >= now - dt.timedelta(days=90)) & (pl.col("horizon_days") >= 30)
    )
    record["maker_taker_gap_t90"] = round(float(fills["gap"].mean()), 4) if len(fills) else None
    record["n_fills_t90"] = len(fills)

    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a") as f:
        f.write(json.dumps(record) + "\n")

    lines = [f"# Edge health — {now:%Y-%m-%d}", ""]
    for name, e in record["cells"].items():
        t90, t365 = e["t90"], e["t365"]
        lines.append(
            f"- **{name}**: {e['light']} — trailing-90d "
            f"{t90['mean']:+.1%} ± {t90['se']:.1%} (n={t90['n']})" if t90["mean"] is not None
            else f"- **{name}**: {e['light']} — insufficient resolved snapshots in 90d window (n={t90['n']})"
        )
        if t365["mean"] is not None:
            lines.append(f"  - trailing-365d {t365['mean']:+.1%} ± {t365['se']:.1%} (n={t365['n']}) · baseline {e['baseline']:+.1%}")
    lines.append("")
    lines.append("## Edge by resolution quarter (decay watch)")
    for name, spec in CELLS.items():
        cell = cell_frame(df, spec).with_columns(
            (pl.col("resolve_ts").dt.year().cast(pl.String) + "-Q"
             + pl.col("resolve_ts").dt.quarter().cast(pl.String)).alias("quarter")
        )
        trend = cell_stats(cell, ["quarter"], "ann_no_carry").filter(pl.col("n") >= 10).tail(8)
        parts = [
            f"{r['quarter']} {r['ann_no_carry_mean']:+.0%}±{r['ann_no_carry_se']:.0%}(n={r['n']})"
            for r in trend.iter_rows(named=True)
        ]
        lines.append(f"- **{name}**: " + " · ".join(parts))
    lines.append("")
    lines.append(f"- calibration gap (≥30d, resolved last 90d): {record['calibration_gap_t90']}")
    lines.append(f"- maker−taker gap (≥30d fills, last 90d): {record['maker_taker_gap_t90']} over {record['n_fills_t90']:,} fills")
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "edge_health.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return record


if __name__ == "__main__":
    run()
