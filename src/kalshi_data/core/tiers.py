"""Universe tier classification, per phase0-assumptions.md section 4.

Tiers:
  excluded        - KXMVE* parlay markets; never ingested beyond a volume tally
  instrumentation - sports and crypto; measured for microstructure, never traded
  deployment      - every other category; eligible for structural research
"""

from __future__ import annotations

import re

import polars as pl

EXCLUDED_TICKER_PREFIXES = ("KXMVE",)
INSTRUMENTATION_CATEGORIES = {"sports", "crypto"}
SPORTS_TITLE_RE = re.compile(
    r"\b(?:sports?|esports|athlete|baseball|basketball|football|hockey|soccer|"
    r"tennis|golf|golfer|cricket|boxing|wrestling|wrestler|olympics?|super bowl|"
    r"world cup|stanley cup|mlb|nba|nfl|nhl|wnba|ncaa|cfb|atp|uefa|fifa|ufc|madden)\b",
    re.IGNORECASE,
)
SPORTS_TITLE_EXCEPTIONS = ("nba youngboy", "nba younbo")
CRYPTO_TITLE_RE = re.compile(
    r"\b(?:crypto(?:currency|currencies)?|bitcoin|ethereum|solana|dogecoin|"
    r"stablecoins?|blockchain|coinbase|binance|btc|eth)\b",
    re.IGNORECASE,
)
OPAQUE_SPORTS_SERIES = {
    "KXBARKLEYMENTION",
    "KXCENAMENTION",
    "KXGAMEDAYMENTION",
    "KXGILLISESPYS",
    "KXINFANTINOMENTION",
    "KXLEBRONMENTION",
    "KXMARMADUNCSDS",
    "KXMICHIGANCOACH",
    "KXMICH",
    "KXNADALMENTION",
    "KXPAULMENTION",
    "KXPORTNOYMENTION",
    "KXSASMITH",
    "KXSHAQMENTION",
    "KXSNFMENTION",
    "KXTNFMENTION",
    "MICHIGANCOACH",
    "MICH",
    "NEWCOACHLAL",
}


def _sports_series(ticker: str, title: str | None, tags: list[str] | None) -> bool:
    if ticker in OPAQUE_SPORTS_SERIES:
        return True
    normalized_title = (title or "").lower()
    if any(exception in normalized_title for exception in SPORTS_TITLE_EXCEPTIONS):
        return False
    normalized_tags = {str(tag).strip().lower() for tag in (tags or [])}
    return "sports" in normalized_tags or bool(SPORTS_TITLE_RE.search(normalized_title))


def _crypto_series(title: str | None, tags: list[str] | None) -> bool:
    normalized_tags = {str(tag).strip().lower() for tag in (tags or [])}
    return "crypto" in normalized_tags or bool(CRYPTO_TITLE_RE.search(title or ""))


def classify(
    ticker: str,
    category: str | None,
    title: str | None = None,
    tags: list[str] | None = None,
) -> str:
    t = (ticker or "").upper()
    if any(t.startswith(p) for p in EXCLUDED_TICKER_PREFIXES):
        return "excluded"
    c = (category or "").lower()
    if (
        c in INSTRUMENTATION_CATEGORIES
        or _sports_series(t, title, tags)
        or _crypto_series(title, tags)
    ):
        return "instrumentation"
    return "deployment"


def apply_current_tiers(markets: pl.DataFrame, series: pl.DataFrame) -> pl.DataFrame:
    """Replace stale raw-market tiers with the current versioned series decision."""
    raw = markets.rename({"tier": "raw_tier"})
    current = series.select(
        pl.col("ticker").alias("series_ticker"),
        pl.col("tier").alias("current_tier"),
    ).unique("series_ticker")
    return raw.join(current, on="series_ticker", how="left").with_columns(
        pl.coalesce("current_tier", "raw_tier").alias("tier")
    ).drop("current_tier", "raw_tier")
