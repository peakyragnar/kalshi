"""Phase 3: the calibration map and go/no-go gate.

Evaluation grid: category x horizon x price bucket, NO-side maker economics with
carry. Pre-committed cascade for thin cells (phase0-assumptions.md section 5):
fine cell needs >= 50 discovery snapshots; else merge adjacent price buckets;
else pool categories at the same horizon x merged bucket; else "insufficient".

Qualification (both must hold, ann_no_carry):
  discovery:    mean - 2*clustered_SE > 7%
  confirmation: mean - 2*clustered_SE > 7%

Void risk is NOT charged here: voided markets never appear under
status=settled, so their frequency is unmeasurable from this dataset. It is
carried as a rulebook-risk item in the Phase 4 memos instead.
"""

from __future__ import annotations

import json

import polars as pl

from .screen_b import no_returns
from .screens import cell_stats, prepare

from ..core.paths import BOOKS, DERIVED, RESEARCH as REPORTS_DIR, SERIES, TRADES

HURDLE = 0.07
MIN_PERIOD_N = 50

COARSE = {
    "01-5": "01-10", "05-10": "01-10",
    "10-20": "10-30", "20-30": "10-30",
    "30-40": "30-50", "40-50": "30-50",
    "50-60": "50-70", "60-70": "50-70",
    "70-80": "70-90", "80-90": "70-90",
    "90-95": "90-99", "95-99": "90-99",
}


def _period_stats(df: pl.DataFrame, cols: list[str]) -> pl.DataFrame:
    out = None
    for period, tag in (("discovery", "disc"), ("confirmation", "conf")):
        s = (
            cell_stats(df.filter(pl.col("period") == period), cols, "ann_no_carry")
            .rename(
                {
                    "n": f"n_{tag}",
                    "n_events": f"ev_{tag}",
                    "ann_no_carry_mean": f"mean_{tag}",
                    "ann_no_carry_se": f"se_{tag}",
                }
            )
        )
        out = s if out is None else out.join(s, on=cols, how="full", coalesce=True)
    return out


def _qualified() -> pl.Expr:
    return (
        (pl.col("n_disc") >= MIN_PERIOD_N)
        & (pl.col("n_conf") >= MIN_PERIOD_N)
        & ((pl.col("mean_disc") - 2 * pl.col("se_disc")) > HURDLE)
        & ((pl.col("mean_conf") - 2 * pl.col("se_conf")) > HURDLE)
    ).fill_null(False)


def build_map(df: pl.DataFrame) -> pl.DataFrame:
    """df: prepared snapshots with ann_no_carry, period, category, horizon_days,
    bucket, event_ticker. Returns evaluation rows across the pooling cascade."""
    df = df.with_columns(pl.col("bucket").replace_strict(COARSE, default=None).alias("coarse"))

    fine = _period_stats(df, ["category", "horizon_days", "bucket"])
    fine_ok = fine.filter(pl.col("n_disc").fill_null(0) >= MIN_PERIOD_N).with_columns(
        pl.lit("fine").alias("level")
    )
    rest1 = df.join(
        fine_ok.select("category", "horizon_days", "bucket"),
        on=["category", "horizon_days", "bucket"],
        how="anti",
    )

    merged = _period_stats(rest1, ["category", "horizon_days", "coarse"])
    merged_ok = merged.filter(pl.col("n_disc").fill_null(0) >= MIN_PERIOD_N).with_columns(
        pl.lit("merged").alias("level")
    )
    rest2 = rest1.join(
        merged_ok.select("category", "horizon_days", "coarse"),
        on=["category", "horizon_days", "coarse"],
        how="anti",
    )

    pooled = _period_stats(rest2, ["horizon_days", "coarse"]).with_columns(
        pl.when(pl.col("n_disc").fill_null(0) >= MIN_PERIOD_N)
        .then(pl.lit("pooled"))
        .otherwise(pl.lit("insufficient"))
        .alias("level"),
        pl.lit("(all)").alias("category"),
    )

    rows = pl.concat(
        [
            fine_ok.rename({"bucket": "bucket_label"}),
            merged_ok.rename({"coarse": "bucket_label"}),
            pooled.rename({"coarse": "bucket_label"}),
        ],
        how="diagonal",
    ).with_columns(_qualified().alias("qualified"))
    return rows.sort(
        ["qualified", "mean_conf"], descending=[True, True], nulls_last=True
    )


def capacity_from_books() -> pl.DataFrame:
    """Latest book per open market -> restable NO-side dollars by category x coarse bucket."""
    series_cat = dict(
        pl.read_parquet(SERIES).select("ticker", "category").iter_rows()
    )
    latest: dict[str, dict] = {}
    for path in sorted(BOOKS.glob("books_*.jsonl")):
        with path.open() as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                latest[rec["ticker"]] = rec
    rows = []
    for ticker, rec in latest.items():
        no_levels = rec.get("no") or []
        if not no_levels:
            continue
        best_no = float(no_levels[-1][0])
        yes_price = round((1 - best_no) * 100)
        if not (1 <= yes_price <= 99):
            continue
        depth_usd = sum(float(p) * float(q) for p, q in no_levels[-3:])
        bucket = next(
            (c for f, c in COARSE.items()
             if int(f.split("-")[0]) <= yes_price < (int(f.split("-")[1]) if f != "95-99" else 100)),
            None,
        )
        series = "KX" + ticker.split("-")[0].removeprefix("KX")
        rows.append(
            {
                "category": series_cat.get(series.split("-")[0], series_cat.get(ticker.split("-")[0])),
                "bucket_label": bucket,
                "depth_usd": depth_usd,
            }
        )
    return (
        pl.DataFrame(rows)
        .drop_nulls()
        .group_by(["category", "bucket_label"])
        .agg(
            pl.col("depth_usd").sum().round(0).alias("restable_usd_now"),
            pl.len().alias("open_markets"),
        )
    )


def _md(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        out.append(
            "| " + " | ".join("" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v)) for v in row) + " |"
        )
    return out


def run() -> None:
    snapshots = pl.read_parquet(DERIVED / "snapshots.parquet")
    trade_counts = (
        pl.scan_parquet(TRADES / "*.parquet")
        .group_by("ticker")
        .agg(pl.len().alias("n_trades"))
        .collect()
    )
    df = no_returns(prepare(snapshots, trade_counts)).filter(pl.col("horizon_days") >= 30)
    rows = build_map(df)

    cap = capacity_from_books().rename({"bucket_label": "cap_bucket"})
    rows = rows.with_columns(
        pl.col("bucket_label").replace(COARSE).alias("cap_bucket")
    ).join(cap, on=["category", "cap_bucket"], how="left").drop("cap_bucket")

    q = rows.filter(pl.col("qualified"))
    lines = ["# Phase 3 — calibration map and go/no-go", ""]
    lines.append(
        f"Evaluation rows: **{len(rows)}** (fine {len(rows.filter(pl.col('level')=='fine'))}, "
        f"merged {len(rows.filter(pl.col('level')=='merged'))}, "
        f"pooled {len(rows.filter(pl.col('level')=='pooled'))}, "
        f"insufficient {len(rows.filter(pl.col('level')=='insufficient'))})."
    )
    lines.append(f"\n**Qualifying cells: {len(q)}**  (rule: mean − 2·clustered SE > 7% and n ≥ 50 in BOTH periods)")
    lines.append("")
    lines.append("## Qualifying cells")
    show = [
        "level", "category", "horizon_days", "bucket_label",
        "n_disc", "mean_disc", "se_disc", "n_conf", "mean_conf", "se_conf",
        "restable_usd_now", "open_markets",
    ]
    lines.extend(_md(q.select(show)) if len(q) else ["*(none — stop rule applies)*"])
    lines.append("")
    lines.append("## Near-misses (confirmation mean > hurdle but fails the 2-SE bar)")
    near = rows.filter(
        (~pl.col("qualified")) & (pl.col("mean_conf") > HURDLE) & (pl.col("n_conf") >= 50)
    ).head(15)
    lines.extend(_md(near.select(show)))
    lines.append("")
    lines.append("## Full map (all evaluation rows)")
    lines.extend(_md(rows.select(show)))
    lines.append("")
    lines.append(
        "Void risk unmeasurable from settled data (voided markets never reach "
        "status=settled); carried as rulebook risk in Phase 4. Capacity = top-3 "
        "NO-side restable dollars in the latest book snapshot, category x bucket "
        "(horizon-agnostic v1)."
    )
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "phase3_map.md").write_text("\n".join(lines))
    print(f"map written: reports/phase3_map.md | evaluation rows {len(rows)} | QUALIFYING {len(q)}")


if __name__ == "__main__":
    run()
