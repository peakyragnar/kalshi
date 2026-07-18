"""Pull the full series catalog and classify each series into a universe tier.

Output: data/series.parquet - one row per series, the join target for everything else.
"""

from __future__ import annotations

import json

import polars as pl

from ..core.client import KalshiClient
from ..core.tiers import classify

from ..core.paths import RAW as DATA_DIR, SERIES


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
                    "tier": classify(
                        s.get("ticker"), s.get("category"), s.get("title"), s.get("tags")
                    ),
                    "settlement_sources": json.dumps(s.get("settlement_sources")),
                    "tags": json.dumps(s.get("tags")),
                }
            )
    df = pl.DataFrame(rows).unique(subset="ticker", keep="first")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(SERIES)
    print(f"series: {len(df):,} rows -> {SERIES}")
    print(df.group_by("tier").len().sort("tier"))
    return df


if __name__ == "__main__":
    run()
