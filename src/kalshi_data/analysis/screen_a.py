"""Screen A: calibration and favorite-longshot bias, by price bucket x horizon."""

from __future__ import annotations


import polars as pl

from .screens import cells, prepare

from ..core.paths import DERIVED, TRADES, RESEARCH as REPORTS_DIR


def _md(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        out.append("| " + " | ".join("" if v is None else str(v) for v in row) + " |")
    return out


def run() -> None:
    snapshots = pl.read_parquet(DERIVED / "snapshots.parquet")
    trade_counts = (
        pl.scan_parquet(TRADES / "*.parquet")
        .group_by("ticker")
        .agg(pl.len().alias("n_trades"))
        .collect()
    )
    df = prepare(snapshots, trade_counts)

    lines = ["# Screen A — calibration and favorite-longshot bias", ""]
    lines.append(
        f"Snapshots after pre-committed filters: **{len(df):,}** "
        f"(from {len(snapshots):,} raw)."
    )
    lines.append("")
    for period in ("discovery", "confirmation"):
        sub = df.filter(pl.col("period") == period)
        lines.append(f"## {period.capitalize()} period — bucket x horizon")
        lines.append("")
        table = cells(sub, ["horizon_days", "bucket"])
        lines.extend(_md(table))
        lines.append("")

    lines.append("## Category x horizon (all buckets pooled)")
    lines.append("")
    table = cells(df, ["period", "horizon_days", "category"])
    lines.extend(_md(table))

    report = "\n".join(lines)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "screen_a.md").write_text(report)
    print(f"screen A written: reports/screen_a.md ({len(df):,} snapshots analyzed)")


if __name__ == "__main__":
    run()
