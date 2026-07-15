"""Phase 1 QA gate: coverage report over the ingested markets dataset."""

from __future__ import annotations

from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def _md_table(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        cells = [f"{v:,}" if isinstance(v, (int, float)) and v is not None else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def run() -> str:
    df = pl.read_parquet(DATA_DIR / "markets" / "*.parquet")
    df = df.with_columns(
        pl.col("close_time").str.to_datetime(time_zone="UTC", strict=False).dt.year().alias("year")
    )
    lines = ["# Phase 1 coverage report", ""]
    lines.append(f"Total settled markets ingested: **{len(df):,}**")
    lines.append("")

    lines.append("## Markets by tier x category x year")
    by_cat = (
        df.group_by(["tier", "category", "year"])
        .agg(pl.len().alias("markets"), pl.col("volume").sum().alias("volume"))
        .sort(["tier", "category", "year"])
    )
    lines.extend(_md_table(by_cat))
    lines.append("")

    lines.append("## Activity filter (assumptions sheet section 4)")
    for threshold in (1, 25, 100):
        n = len(df.filter(pl.col("volume") >= threshold))
        lines.append(f"- volume >= {threshold}: {n:,} markets ({n / len(df):.1%})")
    lines.append("")

    lines.append("## Review-tier categories needing a mapping decision")
    review = (
        df.filter(pl.col("tier") == "review").group_by("category").len().sort("len", descending=True)
    )
    lines.extend(_md_table(review) if len(review) else ["*(none)*"])

    report = "\n".join(lines)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "coverage.md").write_text(report)
    print(report)
    return report


if __name__ == "__main__":
    run()
