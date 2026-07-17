"""Family-level base rates for two legacy candidate cells (Track 3, pipeline 3).

The original map qualified two cells on their average edge. Correct close-time
anchoring later withdrew Financials and left Politics under-supported. This
audit remains a descriptive selection layer; it cannot qualify either cell.

Two tiers, because power and precision trade off:

  Tier 1 — strict (as-traded). Exactly the qualified-cell population, same
  prepare/no_returns machinery, filters, fees, carry and event clustering as
  the map (Politics 30d anchor 1-5c; Financials 90d anchor 1-10c). Verdicts
  here are in-cell proof. First run (2026-07-17): 906 snapshots over 364
  families — no family clears the evidence floor; the tier exists so growing
  history accumulates into it.

  Tier 2 — neighborhood (outcome prior). A settled OUTCOME is a valid
  observation regardless of liquidity: the return filters (>=25 trades,
  staleness) exist to make prices tradeable, not to validate outcomes. So
  tier 2 measures tail frequency on the unfiltered snapshot grid, price used
  only to classify a market as a longshot (<=15c), one row per market
  (anchor nearest the cell's own), clustered by event. Politics anchors
  {7,30}; Financials {30,90,180}. Its `implied` is indicative (unfiltered
  prices); no return columns are computed, so FAT is impossible by
  construction at this tier — TRAP evidence travels across nearby prices
  (a family whose 10c tails fire at 16% makes its 4c tails suspect), size-up
  evidence does not.

Pre-committed thresholds (set 2026-07-17 before the first full run; an
exploratory preview earlier the same day used looser filters — see the report's
honesty note — so per-period persistence is reported for every verdict):

  TRAP    tail_rate >= implied AND tail fired in >= 2 distinct events.
          Point estimate says the family loses money gross; two independent
          firings rule out a single-event fluke. Deliberately cheap to
          trigger: wrongly skipping a family costs little, keeping a losing
          family costs real money (veto cheaply, promote expensively).
  THIN    < 8 event clusters, or zero fires with rule-of-three upper band
          above 2x the price (cannot statistically distinguish even a 2x
          overpricing). No verdict; trades at standard size.
  FAT     the family passes the map's own qualification bar alone
          (n >= 50, ann_no_carry mean - 2*clustered SE > 7%) AND the upper
          band of the tail rate sits below the price. Requires tier-1 return
          columns. Eligible for size-up discussion via the memo gate —
          never automatic.
  NEUTRAL everything else; standard size.

Tail-rate band: cluster-aware. Zero fires -> rule of three on EVENT count
(3/n_events), not snapshot count — 46 correlated markets are not 46 draws.
Otherwise normal approx with the CR0 event-clustered SE.

Labels do not touch deployment rules. The skip-list is a proposal for the
operator; wiring any veto into candidates.py is a findings-book + operator
decision (standing rule).
"""

from __future__ import annotations

import datetime as dt
import json

import polars as pl

from .screen_b import no_returns
from .screens import DISCOVERY_END, cell_stats, prepare

from ..core.paths import CANDIDATES, DERIVED, RESEARCH, TRADES

HURDLE = 0.07
MIN_EVENTS = 8
MIN_TRAP_FIRING_EVENTS = 2
RULE_OF_THREE = 3.0
Z = 1.96

CELLS = {
    "Politics": {"horizon": 30, "max_price": 5},
    "Financials": {"horizon": 90, "max_price": 10},
}
NEIGHBORHOOD = {
    "Politics": {"anchors": [30, 7], "max_price": 15},      # preference order
    "Financials": {"anchors": [90, 30, 180], "max_price": 15},
}

FAMILY = ["category", "series_ticker"]


def _any(conds: list[pl.Expr]) -> pl.Expr:
    keep = conds[0]
    for c in conds[1:]:
        keep = keep | c
    return keep


def cell_population(df: pl.DataFrame) -> pl.DataFrame:
    """Tier 1: rows belonging to a legacy candidate cell under its old filters."""
    return df.filter(
        _any(
            [
                (pl.col("category") == cat)
                & (pl.col("horizon_days") == c["horizon"])
                & (pl.col("yes_price_cents") >= 1)
                & (pl.col("yes_price_cents") <= c["max_price"])
                for cat, c in CELLS.items()
            ]
        )
    )


def neighborhood_population(snapshots: pl.DataFrame) -> pl.DataFrame:
    """Tier 2: unfiltered longshot outcomes, one row per market.

    Anchor preference = the cell's own anchor first, so a market snapshotted
    at several horizons contributes its most cell-like price.
    """
    rank = {
        (cat, a): i for cat, c in NEIGHBORHOOD.items() for i, a in enumerate(c["anchors"])
    }
    df = snapshots.filter(
        _any(
            [
                (pl.col("category") == cat)
                & (pl.col("horizon_days").is_in(c["anchors"]))
                & (pl.col("yes_price_cents") >= 1)
                & (pl.col("yes_price_cents") <= c["max_price"])
                for cat, c in NEIGHBORHOOD.items()
            ]
        )
    )
    df = df.with_columns(
        pl.struct(["category", "horizon_days"])
        .map_elements(lambda s: rank.get((s["category"], s["horizon_days"]), 99), return_dtype=pl.Int64)
        .alias("_rank")
    )
    df = df.sort("_rank").unique(subset=["ticker"], keep="first").drop("_rank")
    return df.with_columns(
        (
            (pl.col("snap_ts") + pl.duration(days=pl.col("hold_days")))
            < pl.lit(DISCOVERY_END).str.to_datetime(time_zone="UTC")
        )
        .replace_strict({True: "discovery", False: "confirmation"})
        .alias("period")
    )


def family_stats(df: pl.DataFrame) -> pl.DataFrame:
    """Per-family stats, event-clustered. Return columns only if present in df."""
    tail = cell_stats(df, FAMILY, "result_yes").rename(
        {"result_yes_mean": "tail_rate", "result_yes_se": "tail_se"}
    )
    extra = df.group_by(FAMILY).agg(
        pl.col("ticker").n_unique().alias("n_markets"),
        (pl.col("yes_price_cents").mean() / 100).alias("implied"),
    )
    firing = (
        df.filter(pl.col("result_yes") == 1)
        .group_by(FAMILY)
        .agg(pl.col("event_ticker").n_unique().alias("firing_events"))
    )
    out = (
        tail.join(extra, on=FAMILY)
        .join(firing, on=FAMILY, how="left")
        .with_columns(pl.col("firing_events").fill_null(0))
    )
    if "ann_no_carry" in df.columns:
        ann = cell_stats(df, FAMILY, "ann_no_carry").rename(
            {"ann_no_carry_mean": "ann_mean", "ann_no_carry_se": "ann_se"}
        ).drop("n", "n_events")
        out = out.join(ann, on=FAMILY)
    else:
        out = out.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("ann_mean"),
            pl.lit(None, dtype=pl.Float64).alias("ann_se"),
        )
    return out.sort("n", descending=True)


def add_labels(stats: pl.DataFrame) -> pl.DataFrame:
    """Tail-rate bands + pre-committed labels. Order: TRAP, THIN, FAT, NEUTRAL.

    FAT needs real return stats: null ann columns (tier 2) can never earn it.
    """
    q_hi = (
        pl.when(pl.col("tail_rate") == 0)
        .then(RULE_OF_THREE / pl.col("n_events"))
        .otherwise(pl.col("tail_rate") + Z * pl.col("tail_se"))
        .clip(0.0, 1.0)
    )
    q_lo = (pl.col("tail_rate") - Z * pl.col("tail_se")).clip(0.0, 1.0)
    out = stats.with_columns(q_lo.alias("q_lo"), q_hi.alias("q_hi"))
    trap = (pl.col("tail_rate") >= pl.col("implied")) & (
        pl.col("firing_events") >= MIN_TRAP_FIRING_EVENTS
    )
    thin = (pl.col("n_events") < MIN_EVENTS) | (
        (pl.col("tail_rate") == 0) & (pl.col("q_hi") > 2 * pl.col("implied"))
    )
    fat = (
        (pl.col("n") >= 50)
        & ((pl.col("ann_mean") - 2 * pl.col("ann_se")) > HURDLE)
        & (pl.col("q_hi") < pl.col("implied"))
    ).fill_null(False)
    return out.with_columns(
        pl.when(trap)
        .then(pl.lit("TRAP"))
        .when(thin)
        .then(pl.lit("THIN"))
        .when(fat)
        .then(pl.lit("FAT"))
        .otherwise(pl.lit("NEUTRAL"))
        .alias("label")
    )


def persistence(df: pl.DataFrame, families: pl.DataFrame) -> pl.DataFrame:
    """Per-period tail rate vs price for the labeled families (the peek guard)."""
    return (
        df.join(families.select(FAMILY), on=FAMILY)
        .group_by(FAMILY + ["period"])
        .agg(
            pl.len().alias("n"),
            pl.col("event_ticker").n_unique().alias("n_events"),
            (pl.col("yes_price_cents").mean() / 100).round(4).alias("implied"),
            pl.col("result_yes").mean().round(4).alias("tail_rate"),
        )
        .sort(FAMILY + ["period"])
    )


def _md(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        out.append(
            "| "
            + " | ".join(
                "" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))
                for v in row
            )
            + " |"
        )
    return out


SHOW = [
    "category", "series_ticker", "n", "n_markets", "n_events", "implied",
    "tail_rate", "q_lo", "q_hi", "firing_events", "label",
]


def run() -> None:
    snapshots = pl.read_parquet(DERIVED / "snapshots.parquet")
    trade_counts = (
        pl.scan_parquet(TRADES / "*.parquet")
        .group_by("ticker")
        .agg(pl.len().alias("n_trades"))
        .collect()
    )

    strict = cell_population(no_returns(prepare(snapshots, trade_counts)))
    t1 = add_labels(family_stats(strict))
    t1_verdicts = t1.filter(pl.col("label").is_in(["TRAP", "FAT"]))

    nbhd = neighborhood_population(snapshots)
    t2 = add_labels(family_stats(nbhd))
    t2_traps = t2.filter(pl.col("label") == "TRAP")
    t2_persist = persistence(nbhd, t2_traps) if len(t2_traps) else pl.DataFrame()

    cands = pl.DataFrame(json.loads(CANDIDATES.read_text()))
    labels_all = (
        pl.concat([t1_verdicts.select(FAMILY + ["label"]), t2_traps.select(FAMILY + ["label"])])
        .unique(subset=FAMILY, keep="first")
        .rename({"series_ticker": "series"})
    )
    overlay = (
        cands.group_by("category", "series")
        .agg(pl.len().alias("on_list_today"))
        .join(labels_all, on=["category", "series"], how="inner")
        .sort("on_list_today", descending=True)
    )

    lines = [f"# Family base rates in legacy candidate cells — {dt.date.today()}", ""]
    lines.append(
        "**Status.** Financials T−90 is withdrawn and Politics T−30 has "
        "insufficient early-fold support. These labels are descriptive only."
    )
    lines.append("")
    lines.append(
        "**Honesty note.** Thresholds were written into the module before the "
        "first full run, but an exploratory preview on 2026-07-17 (looser "
        "filters) had already surfaced two trap suspects. Thresholds were set "
        "on statistical grounds, not tuned to those names; the per-period "
        "persistence table is the guard."
    )
    lines.append("")
    lines.append("## Tier 1 — strict, as-traded (in-cell proof)")
    lines.append(
        f"{len(strict)} snapshots, {t1.height} families. "
        f"Verdicts: {len(t1_verdicts)} "
        f"(THIN {len(t1.filter(pl.col('label') == 'THIN'))}, "
        f"NEUTRAL {len(t1.filter(pl.col('label') == 'NEUTRAL'))})."
    )
    if len(t1_verdicts):
        lines.extend(_md(t1_verdicts.select(SHOW + ["ann_mean", "ann_se"])))
    else:
        lines.append(
            "\n*No family clears the evidence floor inside the strict cell — "
            "the trade's edge rests on the cell average, exactly what the map "
            "validated. This tier accumulates as history grows.*"
        )
    lines.append("")
    lines.append("## Tier 2 — neighborhood outcomes (advisory prior)")
    lines.append(
        f"{len(nbhd)} settled longshot markets (<=15c, unfiltered prices, one "
        f"row per market), {t2.height} families. TRAP {len(t2_traps)}, "
        f"THIN {len(t2.filter(pl.col('label') == 'THIN'))}, "
        f"NEUTRAL {len(t2.filter(pl.col('label') == 'NEUTRAL'))}. "
        "FAT is impossible at this tier by construction."
    )
    lines.append("")
    lines.append("### TRAP families (proposed skip-list)")
    lines.extend(_md(t2_traps.select(SHOW)) if len(t2_traps) else ["*(none)*"])
    lines.append("")
    lines.append("### Persistence by period (discovery = resolved pre-2025-07-01)")
    lines.extend(_md(t2_persist) if len(t2_persist) else ["*(no traps to check)*"])
    lines.append("")
    lines.append("## Today's candidates in verdicted families")
    lines.extend(_md(overlay) if len(overlay) else ["*(none on today's list)*"])
    lines.append("")
    lines.append("## Tier 2 full table (families with >= 8 events)")
    lines.extend(
        _md(t2.filter(pl.col("n_events") >= MIN_EVENTS).sort("tail_rate", descending=True).select(SHOW))
    )
    lines.append("")
    lines.append(
        "Labels are analysis, not rules: wiring TRAP vetoes into the candidate "
        "list requires a findings-book entry and operator sign-off. Tier-2 "
        "implied prices are indicative (unfiltered snapshots)."
    )
    RESEARCH.mkdir(exist_ok=True)
    (RESEARCH / "base_rates.md").write_text("\n".join(lines))
    print(
        f"base rates: tier1 {t1.height} families ({len(t1_verdicts)} verdicts) | "
        f"tier2 {t2.height} families ({len(t2_traps)} TRAP) -> research/base_rates.md"
    )


if __name__ == "__main__":
    run()
