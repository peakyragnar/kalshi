"""Pull the full series catalog and classify each series into a universe tier.

Output: data/series.parquet - one row per series, the join target for everything else.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from .client import KalshiClient
from .tiers import classify

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def run(client: KalshiClient | None = None) -> pl.DataFrame:
    client = client or KalshiClient()
    rows = []
    for page in client.paginate("/series", "series", limit=200):
        for s in page:
            rows.append(
                {
                    "ticker": s.get("ticker"),
                    "title": s.get("title"),
                    "category": s.get("category"),
                    "frequency": s.get("frequency"),
                    "fee_type": s.get("fee_type"),
                    "fee_multiplier": s.get("fee_multiplier"),
                    "tier": classify(s.get("ticker"), s.get("category")),
                    "settlement_sources": json.dumps(s.get("settlement_sources")),
                    "tags": json.dumps(s.get("tags")),
                }
            )
    df = pl.DataFrame(rows).unique(subset="ticker", keep="first")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(DATA_DIR / "series.parquet")
    print(f"series: {len(df):,} rows -> {DATA_DIR / 'series.parquet'}")
    print(df.group_by("tier").len().sort("tier"))
    return df


if __name__ == "__main__":
    run()
