"""Rebuild every registered structural research artifact in dependency order."""

from __future__ import annotations

import json

import polars as pl

from . import atlas, corpus_audit, mechanism_suite, metadata_suite, research_panel, survivor_audit
from ..core.paths import CHECKPOINTS, SERIES


def metadata_backfill_complete() -> bool:
    checkpoint = CHECKPOINTS / "market_metadata_done.json"
    if not checkpoint.exists():
        return False
    done = set(json.loads(checkpoint.read_text()).get("done") or [])
    expected = set(
        pl.read_parquet(SERIES).filter(pl.col("tier") == "deployment")["ticker"].to_list()
    )
    return expected <= done


def run() -> None:
    if not metadata_backfill_complete():
        raise RuntimeError(
            "market metadata backfill is incomplete; run "
            "python -m kalshi_data.ingest.market_metadata first"
        )
    corpus_audit.run()
    research_panel.run()
    atlas.run()
    mechanism_suite.run()
    metadata_suite.run()
    survivor_audit.run()
    print("full structural suite complete", flush=True)


if __name__ == "__main__":
    run()
