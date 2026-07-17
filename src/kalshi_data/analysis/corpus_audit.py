"""Corpus integrity audit and machine-readable coverage table."""

from __future__ import annotations

import datetime as dt

import polars as pl

from .research_panel import normalize_market_times
from ..core.paths import CORPUS_COVERAGE, MARKETS, RESEARCH, TRADES


def audit_corpus(
    markets: pl.DataFrame, trades: pl.DataFrame, now: dt.datetime | None = None
) -> tuple[dict, pl.DataFrame]:
    now = now or dt.datetime.now(dt.timezone.utc)
    m = normalize_market_times(markets).with_columns(
        ((pl.col("scheduled_end_time") - pl.col("open_time")).dt.total_seconds() / 86400).alias("lifetime_days"),
        pl.col("scheduled_end_time").dt.year().alias("scheduled_end_year"),
    ).with_columns(
        pl.when(pl.col("lifetime_days") < 1).then(pl.lit("<1d"))
        .when(pl.col("lifetime_days") < 6).then(pl.lit("1-6d"))
        .when(pl.col("lifetime_days") < 30).then(pl.lit("6-30d"))
        .when(pl.col("lifetime_days") < 90).then(pl.lit("30-90d"))
        .otherwise(pl.lit("90d+")).alias("duration_bucket")
    )
    tape = trades.select("ticker").unique().with_columns(pl.lit(True).alias("has_tape"))
    m = m.join(tape, on="ticker", how="left").with_columns(pl.col("has_tape").fill_null(False))
    traded_short = (pl.col("volume").fill_null(0) >= 1) & (pl.col("lifetime_days") < 6)
    summary = {
        "as_of": now.isoformat(),
        "markets": len(m),
        "events": m["event_ticker"].n_unique(),
        "series": m["series_ticker"].n_unique(),
        "trade_rows": len(trades),
        "markets_with_tape": int(m["has_tape"].sum()),
        "markets_missing_settled_time": int(m["settled_time"].is_null().sum()),
        "result_markets_with_future_scheduled_end": len(m.filter(pl.col("scheduled_end_time") > now)),
        "early_close_markets_without_resolution_time": len(
            m.filter(pl.col("can_close_early").fill_null(False) & pl.col("settled_time").is_null())
        ),
        "traded_sub_6d_markets": len(m.filter(traded_short)),
        "traded_sub_6d_markets_with_tape": len(m.filter(traded_short & pl.col("has_tape"))),
    }
    coverage = m.group_by(
        "category", "scheduled_end_year", "duration_bucket", "has_tape"
    ).agg(
        pl.len().alias("markets"),
        pl.col("event_ticker").n_unique().alias("events"),
        pl.col("series_ticker").n_unique().alias("series"),
        pl.col("volume").fill_null(0).sum().alias("contracts"),
    ).sort("category", "scheduled_end_year", "duration_bucket", "has_tape")
    return summary, coverage


def _markdown(summary: dict, coverage: pl.DataFrame) -> str:
    missing = summary["markets_missing_settled_time"]
    lines = [
        "# Corpus audit",
        "",
        f"Generated: {summary['as_of']}",
        "",
        "## Integrity verdict",
        "",
        "**CONDITIONAL.** Finalized close time provides the historical trading boundary, but actual "
        f"settlement time is missing for **{missing:,}** markets. A decision point is therefore "
        "anchored to close time; settlement time is used for carry only where it is present.",
        "",
        "Historical order books remain unavailable; calibration and fill-conditioned execution claims "
        "are kept separate. Voided/cancelled markets are absent from the settled-only backfill and "
        "must be captured prospectively.",
        "",
        "## Census",
        "",
    ]
    for key, value in summary.items():
        if key != "as_of":
            lines.append(f"- `{key}`: {value:,}" if isinstance(value, int) else f"- `{key}`: {value}")
    lines += ["", "## Coverage", "", "| category | year | duration | tape | markets | events | series | contracts |", "|---|---:|---|---|---:|---:|---:|---:|"]
    for r in coverage.iter_rows(named=True):
        lines.append(
            f"| {r['category']} | {r['scheduled_end_year']} | {r['duration_bucket']} | "
            f"{r['has_tape']} | {r['markets']} | {r['events']} | {r['series']} | {r['contracts']:.0f} |"
        )
    return "\n".join(lines) + "\n"


def run() -> None:
    markets = pl.read_parquet(MARKETS / "*.parquet")
    trades = pl.read_parquet(TRADES / "*.parquet", columns=["ticker", "trade_id"])
    summary, coverage = audit_corpus(markets, trades)
    CORPUS_COVERAGE.parent.mkdir(parents=True, exist_ok=True)
    coverage.write_parquet(CORPUS_COVERAGE)
    RESEARCH.mkdir(exist_ok=True)
    (RESEARCH / "corpus-audit.md").write_text(_markdown(summary, coverage))
    print(f"corpus audit: {summary['markets']:,} markets, {summary['trade_rows']:,} trades")
    print(f"short tape: {summary['traded_sub_6d_markets_with_tape']:,}/{summary['traded_sub_6d_markets']:,}")


if __name__ == "__main__":
    run()
