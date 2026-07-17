"""Append-only, point-in-time external feature store."""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl


KEY = ["source", "entity", "metric", "available_at", "revision"]
REQUIRED = KEY + ["effective_at", "retrieved_at", "value", "evidence"]


def _to_datetime(df: pl.DataFrame, column: str) -> pl.Expr:
    if df.schema[column] == pl.String:
        return pl.col(column).str.to_datetime(time_zone="UTC", strict=False)
    return pl.col(column).cast(pl.Datetime(time_zone="UTC"), strict=False)


def normalize_features(df: pl.DataFrame) -> pl.DataFrame:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"external feature rows missing {', '.join(missing)}")
    out = df.with_columns(
        _to_datetime(df, "effective_at"),
        _to_datetime(df, "available_at"),
        _to_datetime(df, "retrieved_at"),
        pl.col("source").cast(pl.String),
        pl.col("entity").cast(pl.String),
        pl.col("metric").cast(pl.String),
        pl.col("value").cast(pl.String),
        pl.col("revision").cast(pl.String),
        pl.col("evidence").cast(pl.String),
    )
    if out.select((pl.col("retrieved_at") < pl.col("available_at")).any()).item():
        raise ValueError("retrieved_at cannot precede available_at")
    if out.select(
        pl.any_horizontal(
            pl.col("available_at").is_null(), pl.col("retrieved_at").is_null()
        ).any()
    ).item():
        raise ValueError("available_at and retrieved_at are required")
    return out.select(REQUIRED).unique(subset=KEY, keep="last").sort(KEY)


def write_partition(df: pl.DataFrame, path: Path) -> pl.DataFrame:
    out = normalize_features(df)
    if path.exists():
        out = normalize_features(pl.concat([pl.read_parquet(path), out], how="diagonal_relaxed"))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    out.write_parquet(tmp)
    tmp.replace(path)
    return out


def asof_join(points: pl.DataFrame, features: pl.DataFrame, metric: str) -> pl.DataFrame:
    feats = normalize_features(features).filter(pl.col("metric") == metric).rename(
        {
            "available_at": "feature_available_at",
            "value": "feature_value",
            "source": "feature_source",
            "evidence": "feature_evidence",
            "revision": "feature_revision",
            "effective_at": "feature_effective_at",
            "retrieved_at": "feature_retrieved_at",
        }
    )
    return points.sort("decision_time").join_asof(
        feats.sort("feature_available_at"),
        left_on="decision_time",
        right_on="feature_available_at",
        by="entity",
        strategy="backward",
    )
