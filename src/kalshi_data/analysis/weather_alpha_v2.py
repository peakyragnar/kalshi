"""Weather alpha v2: maker-channel economics + out-of-fold recalibration.

Contract: research/weather-alpha-v2.json (registered before first run;
authored from research/weather-alpha-v1-review.md section 4).

Scope of this executable (v2.0): T-1d cells only — the fair-information
horizon. T-6h cells are registered but NOT evaluated until the intraday
running-max capture lands (features/hourly_obs.py backfill); running them
without intraday state would repeat v1's handicap, and running a weakened
version of a registered cell is worse than waiting.

Recalibration: v1 showed the raw model RANKS tails correctly while its
LEVELS are far off (18.5% claimed vs 1.6% realized). The fix is a monotone
bin recalibration fitted on the early (discovery) fold only and applied
out-of-fold: fixed bin edges, Jeffreys-smoothed realized rate per bin,
cumulative-max to enforce monotonicity. Early-fold cell rows are therefore
in-fit and marked; the kill condition reads middle/recent only.
"""

from __future__ import annotations

import bisect
import json
import math

import polars as pl

from .atlas import false_discovery_adjust
from .mechanism_suite import evaluate_cells
from .weather_alpha import build_panel
from ..core.paths import MECHANISM_RESULTS, RESEARCH, WEATHER_V2_CELLS, WEATHER_V2_PERIODS

REGISTRY_PATH = RESEARCH / "weather-alpha-v2.json"
REPORT_PATH = RESEARCH / "weather-alpha-v2-results.md"

CARRY_APY = 0.0325

# pre-committed recalibration bins (fixed before the first v2 run)
BIN_EDGES = [0.0, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 0.95, 0.98, 1.0]

TAIL_THRESHOLDS = (0.002, 0.005, 0.01, 0.02)
DOUBT_MARGINS = (0.02, 0.05, 0.1)


def fit_recalibration(raw: list[float], outcome: list[int]) -> list[float]:
    """Per-bin Jeffreys-smoothed realized rate, monotone via cumulative max.

    Returns one calibrated probability per bin in BIN_EDGES order.
    Empty bins inherit the previous bin's value (monotone continuation).
    """
    n = [0] * (len(BIN_EDGES) - 1)
    fired = [0] * (len(BIN_EDGES) - 1)
    for p, y in zip(raw, outcome):
        index = min(bisect.bisect_right(BIN_EDGES, p) - 1, len(n) - 1)
        n[index] += 1
        fired[index] += int(y)
    out, running = [], 0.0
    for count, hits in zip(n, fired):
        if count:
            value = (hits + 0.5) / (count + 1.0)  # Jeffreys prior
            running = max(running, value)
        out.append(running)
    return out


def apply_recalibration(table: list[float], p: float | None) -> float | None:
    if p is None or not math.isfinite(p):
        return None
    index = min(bisect.bisect_right(BIN_EDGES, p) - 1, len(table) - 1)
    return table[index]


def maker_economics(frame: pl.DataFrame) -> pl.DataFrame:
    """Rest at last print, maker fee only, hold to settlement (the validated channel)."""
    p = pl.col("yes_price_cents").cast(pl.Float64)
    entry = pl.when(pl.col("side") == "yes").then(p).otherwise(100 - p)
    fee = pl.when(pl.col("fee_type") == "quadratic_with_maker_fees").then(
        ((7 * p * (100 - p) + 39999) // 40000).cast(pl.Float64)
    ).otherwise(0.0)
    win = pl.when(pl.col("side") == "yes").then(pl.col("result_yes")).otherwise(1 - pl.col("result_yes"))
    return frame.with_columns(entry.alias("maker_entry_cents")).with_columns(
        ((100 * win - pl.col("maker_entry_cents") - fee) / pl.col("maker_entry_cents")).alias("maker_hold_return")
    ).with_columns(
        (pl.col("maker_hold_return") * (365 * 86400) / pl.col("hold_seconds") + CARRY_APY)
        .alias("maker_annualized_net_return")
    )


def _residualize(frame: pl.DataFrame, base: pl.DataFrame) -> pl.DataFrame:
    """Incremental return vs the family's matched market-only baseline."""
    baseline = base.group_by("period", "decision_label").agg(
        pl.col("maker_annualized_net_return").mean().alias("baseline_return")
    )
    return frame.join(baseline, on=["period", "decision_label"], how="left").with_columns(
        (pl.col("maker_annualized_net_return") - pl.col("baseline_return")).alias("incremental_return")
    )


def _cellize(frame: pl.DataFrame, family: str, cell: pl.Expr) -> pl.DataFrame:
    return frame.with_columns(
        pl.lit(family).alias("family_id"), cell.alias("cell_id"),
        pl.col("maker_annualized_net_return").alias("annualized_net_return"),
    ).select("family_id", "cell_id", "period", "event_ticker", "annualized_net_return", "incremental_return")


def build_v2_frames(panel: pl.DataFrame, labels: tuple[str, ...] = ("T-1d",)) -> dict[str, pl.DataFrame]:
    base = panel.filter(
        (pl.col("side") == "no")
        & pl.col("decision_label").is_in(list(labels))
        & pl.col("calibrated_probability_yes").is_not_null()
    )
    base = maker_economics(base)

    tails = base.filter(pl.col("yes_price_cents") <= 5)
    tail_rows = []
    for threshold in TAIL_THRESHOLDS:
        tail_rows.append(
            _residualize(tails.filter(pl.col("calibrated_probability_yes") <= threshold), tails)
            .pipe(_cellize, "tail-veto-no",
                  pl.format("{}|p<={}|01-05|no", pl.col("decision_label"), pl.lit(str(threshold))))
        )

    favorites = base.filter(pl.col("yes_price_cents") >= 96)
    fav_rows = []
    for margin in DOUBT_MARGINS:
        doubt = (pl.col("yes_price_cents") / 100 - pl.col("calibrated_probability_yes")) >= margin
        fav_rows.append(
            _residualize(favorites.filter(doubt), favorites)
            .pipe(_cellize, "favorite-fragility-no",
                  pl.format("{}|doubt>={}|96-99|no", pl.col("decision_label"), pl.lit(str(margin))))
        )
    return {
        "tail-veto-no": pl.concat(tail_rows),
        "favorite-fragility-no": pl.concat(fav_rows),
    }


# walk-forward fit sources per evaluation fold (registry change-log entry 2):
# each fold's calibration uses only strictly earlier folds; early is in-fit.
WALK_FORWARD = {
    "early": ("early",),
    "middle": ("early",),
    "recent": ("early", "middle"),
    "forward": ("early", "middle", "recent"),
}


def add_calibrated_probability(panel: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, list[float]]]:
    fit_pool = panel.filter(
        (pl.col("side") == "yes") & pl.col("model_probability_yes").is_not_null()
    ).unique(subset=["ticker", "decision_label"])
    tables: dict[str, list[float]] = {}
    for fold, sources in WALK_FORWARD.items():
        rows = fit_pool.filter(pl.col("period").is_in(list(sources)))
        tables[fold] = fit_recalibration(
            rows["model_probability_yes"].to_list(),
            rows["result_yes"].cast(pl.Int64).to_list(),
        )
    out = panel.with_columns(
        pl.struct("model_probability_yes", "period").map_elements(
            lambda s: apply_recalibration(
                tables.get(s["period"], tables["recent"]), s["model_probability_yes"]
            ),
            return_dtype=pl.Float64,
        ).alias("calibrated_probability_yes")
    )
    return out, tables


def kill_condition_check(panel: pl.DataFrame) -> pl.DataFrame:
    """Out-of-fold monotone separation of realized tail rates (middle+recent, T-1d)."""
    tails = panel.filter(
        (pl.col("side") == "yes") & (pl.col("decision_label") == "T-1d")
        & (pl.col("yes_price_cents") <= 5) & pl.col("period").is_in(["middle", "recent"])
        & pl.col("calibrated_probability_yes").is_not_null()
    ).unique(subset=["ticker"])
    edges = [0.0, *TAIL_THRESHOLDS, 1.0]
    labels = [f"({edges[i]}, {edges[i+1]}]" for i in range(len(edges) - 1)]
    banded = tails.with_columns(
        pl.col("calibrated_probability_yes").cut(list(TAIL_THRESHOLDS), labels=labels).alias("band")
    )
    return banded.group_by("band").agg(
        pl.len().alias("n"),
        pl.col("event_ticker").n_unique().alias("events"),
        (pl.col("yes_price_cents").mean() / 100).round(4).alias("market_implied"),
        pl.col("result_yes").mean().round(4).alias("realized"),
    ).sort("band")


def combined_correction(v2_cells: pl.DataFrame) -> pl.DataFrame:
    """Family FDR inside v2, then combined BH across v2 + the structural suite."""
    v2_cells = v2_cells.with_columns(
        pl.when((pl.col("n_periods") == 3) & (pl.col("minimum_fold_events") >= 50))
        .then(pl.col("worst_period_p")).otherwise(1.0).alias("search_p")
    )
    pieces = []
    for _, family in v2_cells.partition_by("family_id", as_dict=True).items():
        q = false_discovery_adjust(family["search_p"].to_list())
        pieces.append(family.with_columns(pl.Series("family_fdr_q", q)))
    v2_cells = pl.concat(pieces)
    structural = pl.read_parquet(MECHANISM_RESULTS).select("search_p")
    combined = v2_cells["search_p"].to_list() + structural["search_p"].to_list()
    q_all = false_discovery_adjust(combined)[: v2_cells.height]
    return v2_cells.with_columns(pl.Series("combined_suite_q", q_all)).with_columns(
        (
            pl.col("passes_all_folds") & (pl.col("family_fdr_q") <= 0.05) & (pl.col("combined_suite_q") <= 0.05)
        ).alias("historically_qualified")
    )


def _md(df: pl.DataFrame) -> list[str]:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        out.append("| " + " | ".join(
            "" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v)) for v in row
        ) + " |")
    return out


def run() -> None:
    registry = json.loads(REGISTRY_PATH.read_text())
    panel, tables = add_calibrated_probability(build_panel())
    frames = build_v2_frames(panel)
    period_parts, cell_parts = [], []
    for family_id, frame in frames.items():
        periods, cells = evaluate_cells(frame, 50, 0.07, 2.0, require_incremental=True)
        period_parts.append(periods)
        cell_parts.append(cells)
    cells = combined_correction(pl.concat(cell_parts))
    periods = pl.concat(period_parts)
    WEATHER_V2_CELLS.parent.mkdir(parents=True, exist_ok=True)
    cells.write_parquet(WEATHER_V2_CELLS)
    periods.write_parquet(WEATHER_V2_PERIODS)

    kill = kill_condition_check(panel)
    survivors = cells.filter(pl.col("historically_qualified"))
    lines = [
        "# Weather alpha v2.0 — maker channel + out-of-fold recalibration",
        "",
        f"Registry: `{REGISTRY_PATH.name}` (v{registry['version']}). Scope: T-1d only; "
        "T-6h cells await the intraday running-max capture (running them without it "
        "would repeat v1's handicap). Early fold is in-fit for the recalibration and "
        "is reported but the kill condition reads middle/recent only.",
        "",
        "Walk-forward recalibration tables (per pre-committed bin):",
        "",
        *(
            f"- {fold} (fit on {'+'.join(WALK_FORWARD[fold])}): "
            + ", ".join(f"{v:.4f}" for v in tables[fold])
            for fold in ("middle", "recent")
        ),
        "",
        "## Kill-condition check — out-of-fold separation (middle+recent, T-1d, <=5c)",
        "",
        *_md(kill),
        "",
        "## Cells",
        "",
        *_md(cells.select(
            "family_id", "cell_id", "n_periods", "minimum_fold_events",
            "worst_lower_bound", "worst_incremental_lower_bound",
            "family_fdr_q", "combined_suite_q", "passes_all_folds", "historically_qualified",
        )),
        "",
        f"**Suite survivors: {survivors.height}**",
        "",
        "Maker economics primary per contract; historical qualification is not "
        "deployment; forward confirmation on sealed data and the deployment ladder "
        "still apply.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(
        f"weather v2.0: {cells.height} cells | survivors {survivors.height} | "
        f"kill check bands: {kill.height} -> {REPORT_PATH.name}", flush=True,
    )


if __name__ == "__main__":
    run()
