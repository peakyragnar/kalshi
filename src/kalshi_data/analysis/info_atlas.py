"""Information-edge atlas: rank every market family by modelability.

Track A of docs/plans/03-information-edge-plan.md. The search space for
information edges is not "all data" — it is Kalshi's settlement variables.
Each series family is scored on six axes; the ranking is the data-acquisition
priority list for the model program.

Pre-committed scoring (fixed 2026-07-18, before the first ranked run):

  A1 mechanicalness   settlement-source class: government 1.0,
                      exchange_or_data 0.8, media_or_other 0.2, missing 0.1
  A2 upstream signal  automated proposal from settlement-source hostnames;
                      the hostname catalog below maps known publishers to a
                      point-in-time archive verdict. Families outside the
                      catalog score the UNKNOWN floor (0.3) pending the
                      per-family judgment pass — unknown is not zero, and
                      it is not a verdict.
  A3 point-in-time    from the same catalog: 1.0 archives exist,
                      0.5 capture-only (must record forward), 0.1 none known
  A4 dumb-flow depth  contracts where a taker crossed at extreme YES prices
                      (<=5c or >=96c) into a resting maker, trailing corpus;
                      log-normalized to the max family
  A5 tail mispricing  implied-minus-realized YES rate in the extreme buckets
                      at T-1d decisions (positive = overpriced tails = maker
                      wage); floor at 0, cap at 0.05, linear scale; families
                      with < 100 extreme-price decisions score the UNKNOWN
                      floor (0.3) — thin evidence is not a verdict
  A6 verification     settled markets per month, trailing 12 months,
                      log-normalized to the max family

  rank_score = geometric mean of the six axis scores. A structural zero on
  A1 (missing source AND no catalog entry) zeroes the family.

The atlas is descriptive research: it prioritizes data acquisition. It
qualifies nothing and changes no deployment rule.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from urllib.parse import urlparse

import polars as pl

from .mechanism_suite import classify_settlement_source
from .screen_d import load as load_fills
from ..core.paths import DECISION_POINTS, DERIVED, OUTCOMES, RESEARCH, RULEBOOK_VERDICTS, SERIES

ATLAS_PARQUET = DERIVED / "info_atlas.parquet"
ATLAS_REPORT = RESEARCH / "information-edge-atlas.md"

MECHANICALNESS = {"government": 1.0, "exchange_or_data": 0.8, "media_or_other": 0.2, "missing": 0.1}
UNKNOWN_FLOOR = 0.3
TAIL_GAP_CAP = 0.05
MIN_TAIL_DECISIONS = 100

# hostname catalog: known settlement publishers -> (upstream score, point-in-time
# score, note). Point-in-time: 1.0 = public archives of the as-of state exist;
# 0.5 = state is public but must be captured forward; 0.1 = no known trail.
HOST_CATALOG: dict[str, tuple[float, float, str]] = {
    "weather.gov": (1.0, 1.0, "NWS/NOAA: model-run archives (GFS et al.) + station obs"),
    "noaa.gov": (1.0, 1.0, "NOAA: model-run archives + NCEI daily summaries"),
    "ncei.noaa.gov": (1.0, 1.0, "NCEI daily summaries"),
    "nhc.noaa.gov": (0.9, 1.0, "NHC advisories are archived point-in-time"),
    "sec.gov": (0.9, 1.0, "EDGAR: filings timestamped at acceptance"),
    "senate.gov": (0.8, 0.5, "Executive Calendar/cloture: public, capture-only"),
    "congress.gov": (0.8, 0.5, "bill status: public, capture-only"),
    "bls.gov": (0.7, 1.0, "BLS releases + ALFRED vintages"),
    "bea.gov": (0.7, 1.0, "BEA releases + ALFRED vintages"),
    "fred.stlouisfed.org": (0.7, 1.0, "ALFRED point-in-time vintages"),
    "stlouisfed.org": (0.7, 1.0, "ALFRED point-in-time vintages"),
    "eia.gov": (0.8, 1.0, "EIA weekly/monthly releases are versioned"),
    "cdc.gov": (0.7, 0.5, "surveillance data: public, revisions matter, capture"),
    "treasury.gov": (0.7, 1.0, "auction results/rates archived"),
    "federalreserve.gov": (0.3, 1.0, "Fed decisions: upstream IS the professionals' game"),
    "nasdaq.com": (0.6, 1.0, "exchange data: historical prices archived"),
    "nyse.com": (0.6, 1.0, "exchange data: historical prices archived"),
    "cmegroup.com": (0.6, 1.0, "settlement prices archived"),
    "tradingview.com": (0.5, 0.5, "price feeds: capture-only at settlement source"),
    "faa.gov": (0.7, 0.5, "advisories/logs: public, capture-only"),
    "bts.gov": (0.8, 1.0, "transportation statistics archived"),
    # judgment pass 2026-07-18 (plan 03 Track A): entries below added after
    # reviewing the top-30 unknown-floor families by flow
    "gasprices.aaa.com": (0.8, 0.5, "AAA daily national gas price; EIA weekly archived cousin"),
    "federalregister.gov": (0.8, 1.0, "Federal Register: EO publication archived"),
    "opm.gov": (0.7, 0.5, "OPM operating status: public, capture-only"),
    "theice.com": (0.6, 1.0, "ICE settlement prices archived; pro-priced underlying"),
    "rottentomatoes.com": (0.7, 0.5, "scores public; review counts accumulate predictably; capture-only"),
    "lmarena.ai": (0.8, 0.5, "LM Arena leaderboard: public, slow-moving, capture-only"),
    "arena.ai": (0.8, 0.5, "LM Arena leaderboard: public, slow-moving, capture-only"),
    "netflix.com": (0.7, 0.5, "Netflix weekly Top-10: published weekly, capture-only"),
    "spotify.com": (0.7, 0.5, "Spotify charts: published, partial public history"),
    "billboard.com": (0.6, 0.5, "Billboard charts: published weekly"),
    "spacex.com": (0.7, 0.5, "launch counts: schedules + FAA licenses public, capture-only"),
    "nyc.gov": (0.6, 0.5, "city election results: official, capture-only"),
    "usa.gov": (0.5, 0.5, "official results pages: capture-only"),
    "kalshi.com": (0.2, 0.2, "self-referential settlement: no external trail"),
}

# per-series judgment overrides (2026-07-18): applied AFTER host_scores. Two
# reasons a series lands here: Kalshi's settlement_sources metadata is wrong
# (KXMUSKNW cites BLS for a net-worth market), or the real upstream is not
# derivable from hostnames (index ranges: CBOE options smiles are a literal
# probability density for the settlement variable).
SERIES_OVERRIDES: dict[str, tuple[float, float, str]] = {
    "KXMUSKNW": (0.4, 0.5, "metadata wrong (cites BLS); actual: Bloomberg Billionaires, capture-only"),
    "INXY": (0.8, 0.5, "options-implied density (CBOE SPX smile) prices the settlement variable"),
    "NASDAQ100Y": (0.8, 0.5, "options-implied density (CBOE NDX smile) prices the settlement variable"),
    "KXINX": (0.8, 0.5, "options-implied density (CBOE SPX smile) prices the settlement variable"),
    "KXINXY": (0.8, 0.5, "options-implied density (CBOE SPX smile) prices the settlement variable"),
    "KXNASDAQ100": (0.8, 0.5, "options-implied density (CBOE NDX smile) prices the settlement variable"),
    "KXNASDAQ100Y": (0.8, 0.5, "options-implied density (CBOE NDX smile) prices the settlement variable"),
}


def host_scores(settlement_sources: str | None) -> tuple[float, float, str]:
    """(upstream, point_in_time, note) from the best catalog hit among source hosts."""
    try:
        sources = json.loads(settlement_sources or "[]")
    except (json.JSONDecodeError, TypeError):
        sources = []
    best: tuple[float, float, str] | None = None
    for source in sources or []:
        host = (urlparse(str(source.get("url") or "")).hostname or "").removeprefix("www.")
        for suffix, entry in HOST_CATALOG.items():
            if host == suffix or host.endswith("." + suffix):
                if best is None or entry[0] > best[0]:
                    best = entry
    return best if best else (UNKNOWN_FLOOR, UNKNOWN_FLOOR, "no catalog entry — judgment pass pending")


def _log_norm(col: pl.Expr) -> pl.Expr:
    """log1p, normalized to the column max; zero stays zero."""
    v = col.cast(pl.Float64).fill_null(0.0).clip(lower_bound=0.0).log1p()
    return (v / v.max()).fill_nan(0.0)


def tail_gap_score(gap: float | None, n_decisions: int) -> float:
    """A5: positive tail overpricing, capped; thin evidence gets the unknown floor."""
    if n_decisions < MIN_TAIL_DECISIONS or gap is None:
        return UNKNOWN_FLOOR
    return max(0.0, min(gap, TAIL_GAP_CAP)) / TAIL_GAP_CAP


def geometric_mean(scores: list[float]) -> float:
    if any(s <= 0 for s in scores):
        return 0.0
    return math.exp(sum(math.log(s) for s in scores) / len(scores))


def build_atlas() -> pl.DataFrame:
    series = pl.read_parquet(SERIES).select("ticker", "category", "title", "settlement_sources")
    verdicts = json.loads(RULEBOOK_VERDICTS.read_text())
    red = {t for t, v in verdicts.items() if v.get("verdict") == "RED"}
    series = series.filter(
        ~pl.col("ticker").is_in(sorted(red))
        & ~pl.col("category").is_in(["Sports", "Crypto"])
        & ~pl.col("ticker").str.starts_with("KXMVE")
    )

    # A1-A3 from settlement sources
    rows = []
    for r in series.iter_rows(named=True):
        source_class = classify_settlement_source(r["settlement_sources"])
        if r["ticker"] in SERIES_OVERRIDES:
            upstream, pit, note = SERIES_OVERRIDES[r["ticker"]]
            note = "override — " + note
        else:
            upstream, pit, note = host_scores(r["settlement_sources"])
        rows.append({
            "series_ticker": r["ticker"], "category": r["category"], "title": r["title"],
            "source_class": source_class,
            "a1_mechanical": MECHANICALNESS.get(source_class, 0.1),
            "a2_upstream": upstream, "a3_point_in_time": pit, "upstream_note": note,
        })
    atlas = pl.DataFrame(rows)

    # A4: extreme-price crossed flow per family (both tails), full fills corpus
    fills = load_fills().with_columns(
        pl.col("ticker").str.split("-").list.first().alias("series_ticker")
    )
    flow = (
        fills.filter((pl.col("yes_price_cents") <= 5) | (pl.col("yes_price_cents") >= 96))
        .group_by("series_ticker")
        .agg(pl.col("count").sum().alias("extreme_contracts"))
    )

    # A5: tail calibration gap at T-1d decisions; A6: settlement cadence
    points = pl.read_parquet(DECISION_POINTS).filter(
        (pl.col("decision_label") == "T-1d") & pl.col("decision_time_trustworthy")
    ).select("ticker", "series_ticker", "yes_price_cents")
    outcomes = pl.read_parquet(OUTCOMES).select("ticker", "result_yes", "resolution_time")
    joined = points.join(outcomes, on="ticker", how="inner")
    tails = (
        joined.filter((pl.col("yes_price_cents") <= 5) | (pl.col("yes_price_cents") >= 96))
        .with_columns(
            pl.when(pl.col("yes_price_cents") <= 5)
            .then(pl.col("yes_price_cents").cast(pl.Float64) / 100 - pl.col("result_yes"))
            .otherwise((100 - pl.col("yes_price_cents").cast(pl.Float64)) / 100 - (1 - pl.col("result_yes")))
            .alias("tail_gap")
        )
        .group_by("series_ticker")
        .agg(pl.col("tail_gap").mean().alias("tail_gap"), pl.len().alias("tail_decisions"))
    )
    now = dt.datetime.now(dt.timezone.utc)
    cadence = (
        outcomes.join(points.select("ticker", "series_ticker").unique("ticker"), on="ticker")
        .filter(pl.col("resolution_time") > now - dt.timedelta(days=365))
        .group_by("series_ticker")
        .agg((pl.len() / 12.0).alias("settlements_per_month"))
    )

    atlas = (
        atlas.join(flow, on="series_ticker", how="left")
        .join(tails, on="series_ticker", how="left")
        .join(cadence, on="series_ticker", how="left")
        .with_columns(
            pl.col("extreme_contracts").fill_null(0),
            pl.col("tail_decisions").fill_null(0),
            pl.col("settlements_per_month").fill_null(0.0),
        )
        .with_columns(
            _log_norm(pl.col("extreme_contracts")).alias("a4_flow"),
            pl.struct("tail_gap", "tail_decisions").map_elements(
                lambda s: tail_gap_score(s["tail_gap"], s["tail_decisions"]), return_dtype=pl.Float64
            ).alias("a5_tail_gap"),
            _log_norm(pl.col("settlements_per_month")).alias("a6_speed"),
        )
    )
    axis_cols = ["a1_mechanical", "a2_upstream", "a3_point_in_time", "a4_flow", "a5_tail_gap", "a6_speed"]
    return atlas.with_columns(
        pl.struct(axis_cols).map_elements(
            lambda s: geometric_mean([s[c] for c in axis_cols]), return_dtype=pl.Float64
        ).alias("rank_score")
    ).sort("rank_score", descending=True)


def _md_table(df: pl.DataFrame, cols: list[str]) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.select(cols).iter_rows():
        out.append("| " + " | ".join(
            "" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v)[:48]) for v in row
        ) + " |")
    return out


def run() -> None:
    atlas = build_atlas()
    ATLAS_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    atlas.write_parquet(ATLAS_PARQUET)
    show = [
        "series_ticker", "category", "rank_score", "a1_mechanical", "a2_upstream",
        "a3_point_in_time", "a4_flow", "a5_tail_gap", "a6_speed",
        "extreme_contracts", "tail_decisions", "settlements_per_month", "upstream_note",
    ]
    top = atlas.head(40)
    by_cat = (
        atlas.group_by("category")
        .agg(pl.col("rank_score").max().alias("best_rank"), pl.len().alias("families"))
        .sort("best_rank", descending=True)
    )
    lines = [
        f"# Information-edge atlas — {dt.date.today()}",
        "",
        f"{atlas.height} families scored on six pre-committed axes "
        "(see module docstring; geometric mean). Descriptive research: this is a "
        "data-acquisition priority list, not a qualification of anything. "
        "Families with `no catalog entry` on A2/A3 carry the 0.3 unknown floor "
        "and await the judgment pass.",
        "",
        "## Top 40 families",
        "",
        *_md_table(top, show),
        "",
        "## Best rank per category",
        "",
        *_md_table(by_cat, ["category", "best_rank", "families"]),
        "",
        "Machine-readable: `data/derived/info_atlas.parquet`. Refresh quarterly "
        "or on universe change (03-information-edge-plan.md, Track A).",
    ]
    ATLAS_REPORT.write_text("\n".join(lines) + "\n")
    print(f"info atlas: {atlas.height} families -> {ATLAS_REPORT.name}; top: "
          + ", ".join(atlas.head(5)["series_ticker"].to_list()), flush=True)


if __name__ == "__main__":
    run()
