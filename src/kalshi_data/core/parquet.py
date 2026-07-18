"""Parquet shard readers that tolerate schema evolution between batches."""

from __future__ import annotations

from pathlib import Path

import polars as pl


def read_shards(directory: Path, columns: list[str] | None = None) -> pl.DataFrame:
    """Read sorted shards while promoting all-null fields to later concrete types."""
    paths = sorted(directory.glob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no parquet shards in {directory}")
    frames = [pl.read_parquet(path, columns=columns) for path in paths]
    if len(frames) == 1:
        return frames[0]
    return pl.concat(frames, how="diagonal_relaxed")
