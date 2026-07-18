"""Registered external-data alpha research for daily temperature markets."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import polars as pl

from .atlas import add_periods, false_discovery_adjust
from .external_alpha import add_strategy_economics, evaluate_registered_cells
from .mechanism_suite import residualize_against_baseline
from ..core.parquet import read_shards
from ..core.paths import (
    DECISION_POINTS,
    MARKET_METADATA,
    MECHANISM_RESULTS,
    OUTCOMES,
    RESEARCH,
    WEATHER_FORECASTS,
    WEATHER_OBSERVATIONS,
    WEATHER_PANEL,
    WEATHER_PERIODS,
    WEATHER_RESULTS,
)
from ..features.weather import SERIES_TO_STATION, STATIONS, event_target_date


REGISTRY_PATH = RESEARCH / "weather-alpha-v1.json"
REPORT_PATH = RESEARCH / "weather-alpha-results.md"
FUNNEL_PATH = RESEARCH / "weather-alpha-funnel.svg"
DECISION_LABELS = ("T-6h", "T-1d")
SPREAD_RESERVE_CENTS = 2

def attach_rolling_calibration(
    forecasts: pl.DataFrame,
    observations: pl.DataFrame,
    minimum_history: int = 60,
) -> pl.DataFrame:
    """Attach expanding error moments available before each forecast feature."""
    errors = forecasts.join(
        observations.select(
            "station", "weather_stat", "target_date", "observed_f",
            pl.col("available_at").alias("observation_available_at"),
        ),
        on=["station", "weather_stat", "target_date"],
        how="inner",
    ).with_columns(
        (pl.col("observed_f") - pl.col("forecast_f")).alias("forecast_error")
    )
    groups = ["station", "weather_stat", "lead_days"]
    daily = errors.group_by(
        *groups, "target_date"
    ).agg(
        pl.len().alias("date_n"),
        pl.col("forecast_error").sum().alias("date_sum"),
        (pl.col("forecast_error") ** 2).sum().alias("date_sum_sq"),
        pl.col("observation_available_at").max().alias("calibration_available_at"),
    ).sort(*groups, "calibration_available_at").with_columns(
        pl.col("date_n").cum_sum().over(*groups).alias("calibration_n"),
        pl.col("date_sum").cum_sum().over(*groups).alias("calibration_sum"),
        pl.col("date_sum_sq").cum_sum().over(*groups).alias("calibration_sum_sq"),
    )
    joined = forecasts.sort("available_at").join_asof(
        daily.sort("calibration_available_at"),
        left_on="available_at",
        right_on="calibration_available_at",
        by=groups,
        strategy="backward",
        check_sortedness=False,
    )
    enough = pl.col("calibration_n") >= minimum_history
    variance = (
        pl.col("calibration_sum_sq")
        - pl.col("calibration_sum") ** 2 / pl.col("calibration_n")
    ) / (pl.col("calibration_n") - 1)
    return joined.with_columns(
        pl.when(enough).then(
            pl.col("calibration_sum") / pl.col("calibration_n")
        ).alias("calibration_bias_f"),
        pl.when(enough).then(variance.clip(lower_bound=2.25).sqrt()).alias(
            "calibration_sigma_f"
        ),
        pl.when(enough).then(pl.col("calibration_n")).alias("calibration_n"),
    ).drop(
        "date_n", "date_sum", "date_sum_sq", "calibration_sum",
        "calibration_sum_sq", strict=False,
    )


def _cdf(value: float, mean: float, sigma: float) -> float:
    return 0.5 * (1 + math.erf((value - mean) / (sigma * math.sqrt(2))))


def probability_yes(
    strike_type: str | None,
    floor: float | None,
    cap: float | None,
    mean: float,
    sigma: float,
) -> float | None:
    """Translate a continuous daily-temperature distribution into rulebook probability."""
    if not math.isfinite(mean) or not math.isfinite(sigma) or sigma <= 0:
        return None
    if strike_type == "greater" and floor is not None:
        return 1 - _cdf(float(floor) + 0.5, mean, sigma)
    if strike_type == "less" and cap is not None:
        return _cdf(float(cap) - 0.5, mean, sigma)
    if strike_type == "between" and floor is not None and cap is not None:
        return max(
            0.0,
            _cdf(float(cap) + 0.5, mean, sigma)
            - _cdf(float(floor) - 0.5, mean, sigma),
        )
    return None


def _feature_frames() -> tuple[pl.DataFrame, pl.DataFrame]:
    forecasts = pl.read_parquet(WEATHER_FORECASTS).with_columns(
        pl.col("entity").str.split_exact(":", 1).struct.field("field_0").alias("station"),
        pl.col("entity").str.split_exact(":", 1).struct.field("field_1")
        .str.to_date().alias("target_date"),
        pl.when(pl.col("metric").str.contains("max"))
        .then(pl.lit("high")).otherwise(pl.lit("low")).alias("weather_stat"),
        pl.col("revision").str.extract(r"lead(\d+)", 1).cast(pl.Int8).alias("lead_days"),
        pl.col("value").cast(pl.Float64).alias("forecast_f"),
    ).select(
        "station", "weather_stat", "target_date", "lead_days", "forecast_f",
        "available_at", "source", "revision", "evidence",
    )
    observations = pl.read_parquet(WEATHER_OBSERVATIONS).with_columns(
        pl.col("entity").str.split_exact(":", 1).struct.field("field_0").alias("station"),
        pl.col("entity").str.split_exact(":", 1).struct.field("field_1")
        .str.to_date().alias("target_date"),
        pl.when(pl.col("metric").str.contains("max"))
        .then(pl.lit("high")).otherwise(pl.lit("low")).alias("weather_stat"),
        pl.col("value").cast(pl.Float64).alias("observed_f"),
    ).select(
        "station", "weather_stat", "target_date", "observed_f", "available_at"
    )
    return forecasts, observations


def _price_bucket() -> pl.Expr:
    price = pl.col("entry_price_cents")
    return (
        pl.when(price <= 20).then(pl.lit("01-20"))
        .when(price <= 40).then(pl.lit("21-40"))
        .when(price <= 60).then(pl.lit("41-60"))
        .when(price <= 80).then(pl.lit("61-80"))
        .otherwise(pl.lit("81-99")).alias("entry_price_bucket")
    )


def _staleness_bucket() -> pl.Expr:
    fraction = pl.col("price_staleness_seconds") / pl.col("scheduled_hold_seconds")
    return (
        pl.when(fraction <= 0.05).then(pl.lit("fresh"))
        .when(fraction <= 0.20).then(pl.lit("aging"))
        .otherwise(pl.lit("stale")).alias("staleness_bin")
    )


def _probability_expr() -> pl.Expr:
    return pl.struct(
        "strike_type", "floor_strike", "cap_strike",
        "forecast_mean_f", "calibration_sigma_f",
    ).map_elements(
        lambda row: probability_yes(
            row["strike_type"], row["floor_strike"], row["cap_strike"],
            row["forecast_mean_f"], row["calibration_sigma_f"],
        ),
        return_dtype=pl.Float64,
    ).alias("model_probability_yes")


def build_panel(minimum_history: int = 60) -> pl.DataFrame:
    forecasts, observations = _feature_frames()
    forecasts = attach_rolling_calibration(forecasts, observations, minimum_history)
    series = list(SERIES_TO_STATION)
    station_lookup = {key: value.key for key, value in SERIES_TO_STATION.items()}
    stat_lookup = {
        key: ("low" if "LOW" in key else "high") for key in SERIES_TO_STATION
    }
    points = pl.read_parquet(DECISION_POINTS).filter(
        pl.col("series_ticker").is_in(series)
        & pl.col("decision_label").is_in(DECISION_LABELS)
        & pl.col("decision_time_trustworthy")
        & pl.col("yes_price_cents").is_between(1, 99)
        & ~pl.col("is_block_trade").fill_null(False)
    ).with_columns(
        pl.col("series_ticker").replace_strict(station_lookup).alias("station"),
        pl.col("series_ticker").replace_strict(stat_lookup).alias("weather_stat"),
        pl.col("event_ticker").map_elements(
            event_target_date, return_dtype=pl.Date
        ).alias("target_date"),
    ).filter(pl.col("target_date").is_not_null())
    outcomes = pl.read_parquet(OUTCOMES).select(
        "ticker", "result_yes", "resolution_time", "resolution_time_trustworthy"
    )
    metadata = read_shards(
        MARKET_METADATA,
        columns=["ticker", "floor_strike", "cap_strike", "strike_type"],
    ).unique("ticker")
    base = points.join(outcomes, on="ticker", how="inner").join(
        metadata, on="ticker", how="inner"
    ).filter(pl.col("strike_type").is_in(["greater", "less", "between"])).with_columns(
        pl.when(
            pl.col("resolution_time_trustworthy")
            & (pl.col("resolution_time") > pl.col("decision_time"))
        ).then(
            (pl.col("resolution_time") - pl.col("decision_time")).dt.total_seconds()
        ).otherwise(pl.col("scheduled_hold_seconds")).alias("hold_seconds")
    ).filter(pl.col("hold_seconds") > 0)
    candidates = base.join(
        forecasts,
        on=["station", "weather_stat", "target_date"],
        how="inner",
    ).filter(
        (pl.col("available_at") <= pl.col("decision_time"))
        & pl.col("calibration_n").is_not_null()
    ).sort(
        "ticker", "decision_time", "available_at", "lead_days"
    ).unique(["ticker", "decision_time", "decision_label"], keep="last").with_columns(
        (pl.col("forecast_f") + pl.col("calibration_bias_f")).alias("forecast_mean_f")
    ).with_columns(_probability_expr()).filter(
        pl.col("model_probability_yes").is_not_null()
    )
    sides = pl.concat([
        candidates.with_columns(pl.lit("yes").alias("side")),
        candidates.with_columns(pl.lit("no").alias("side")),
    ], how="vertical_relaxed")
    panel = add_strategy_economics(sides, SPREAD_RESERVE_CENTS).with_columns(
        pl.when(pl.col("side") == "yes")
        .then(pl.col("model_probability_yes"))
        .otherwise(1 - pl.col("model_probability_yes")).alias("model_win_probability")
    ).with_columns(
        (
            (pl.col("model_win_probability") - 0.02) * 100
            - pl.col("entry_price_cents") - pl.col("fee_cents")
        ).alias("net_model_edge_cents"),
        _price_bucket(),
        _staleness_bucket(),
    )
    panel = add_periods(panel).filter(pl.col("period") != "forward")
    return residualize_against_baseline(
        panel,
        ["period", "decision_label", "weather_stat", "side", "entry_price_bucket"],
    )


def _load_registry(path: Path = REGISTRY_PATH) -> dict:
    raw = path.read_bytes()
    registry = json.loads(raw)
    if registry.get("version") != 1 or len(registry.get("families") or []) != 5:
        raise ValueError("weather registry requires version=1 and five families")
    registry["sha256"] = hashlib.sha256(raw).hexdigest()
    return registry


def _cell(frame: pl.DataFrame, family: str, parts: list[pl.Expr]) -> pl.DataFrame:
    return frame.with_columns(
        pl.lit(family).alias("family_id"),
        pl.concat_str(parts, separator="|").alias("cell_id"),
    ).select(
        "family_id", "cell_id", "period", "event_ticker",
        "annualized_net_return", "hold_return", "incremental_return",
    )


def _registered_row(family: str, values: tuple[object, ...]) -> dict:
    return {"family_id": family, "cell_id": "|".join(str(value) for value in values)}


def build_family_frames(
    panel: pl.DataFrame, registry: dict
) -> tuple[pl.DataFrame, pl.DataFrame]:
    frames, registered = [], []
    specs = {item["id"]: item for item in registry["families"]}
    level = specs["weather-level-disagreement"]["dimensions"]
    for label in level["decision_labels"]:
        for threshold in level["minimum_net_edges_cents"]:
            for stat in level["weather_stats"]:
                for side in level["sides"]:
                    values = (label, f"edge>={threshold}", stat, side)
                    registered.append(_registered_row("weather-level-disagreement", values))
                    sub = panel.filter(
                        (pl.col("decision_label") == label)
                        & (pl.col("net_model_edge_cents") >= threshold)
                        & (pl.col("weather_stat") == stat)
                        & (pl.col("side") == side)
                    )
                    frames.append(_cell(sub, "weather-level-disagreement", [pl.lit(v) for v in values]))
    city_spec = specs["weather-city-disagreement"]
    threshold = city_spec["fixed_minimum_net_edge_cents"]
    dims = city_spec["dimensions"]
    for station in [item.key for item in STATIONS]:
        for label in dims["decision_labels"]:
            for stat in dims["weather_stats"]:
                for side in dims["sides"]:
                    values = (station, label, stat, side)
                    registered.append(_registered_row("weather-city-disagreement", values))
                    sub = panel.filter(
                        (pl.col("station") == station)
                        & (pl.col("decision_label") == label)
                        & (pl.col("weather_stat") == stat)
                        & (pl.col("side") == side)
                        & (pl.col("net_model_edge_cents") >= threshold)
                    )
                    frames.append(_cell(sub, "weather-city-disagreement", [pl.lit(v) for v in values]))
    price_spec = specs["weather-price-disagreement"]
    threshold = price_spec["fixed_minimum_net_edge_cents"]
    dims = price_spec["dimensions"]
    for label in dims["decision_labels"]:
        for bucket in dims["entry_price_buckets"]:
            for stat in dims["weather_stats"]:
                for side in dims["sides"]:
                    values = (label, bucket, stat, side)
                    registered.append(_registered_row("weather-price-disagreement", values))
                    sub = panel.filter(
                        (pl.col("decision_label") == label)
                        & (pl.col("entry_price_bucket") == bucket)
                        & (pl.col("weather_stat") == stat)
                        & (pl.col("side") == side)
                        & (pl.col("net_model_edge_cents") >= threshold)
                    )
                    frames.append(_cell(sub, "weather-price-disagreement", [pl.lit(v) for v in values]))
    stale_spec = specs["weather-staleness-disagreement"]
    threshold = stale_spec["fixed_minimum_net_edge_cents"]
    dims = stale_spec["dimensions"]
    for label in dims["decision_labels"]:
        for bucket in dims["staleness_bins"]:
            for stat in dims["weather_stats"]:
                for side in dims["sides"]:
                    values = (label, bucket, stat, side)
                    registered.append(_registered_row("weather-staleness-disagreement", values))
                    sub = panel.filter(
                        (pl.col("decision_label") == label)
                        & (pl.col("staleness_bin") == bucket)
                        & (pl.col("weather_stat") == stat)
                        & (pl.col("side") == side)
                        & (pl.col("net_model_edge_cents") >= threshold)
                    )
                    frames.append(_cell(sub, "weather-staleness-disagreement", [pl.lit(v) for v in values]))
    revision_spec = specs["weather-revision-underreaction"]
    minimum_edge = revision_spec["fixed_minimum_net_edge_cents"]
    dims = revision_spec["dimensions"]
    for earlier, later in dims["label_pairs"]:
        old = panel.filter(pl.col("decision_label") == earlier).select(
            "ticker", "side",
            pl.col("model_win_probability").alias("old_model_win_probability"),
            pl.col("entry_price_cents").alias("old_entry_price_cents"),
        )
        paired = panel.filter(pl.col("decision_label") == later).join(
            old, on=["ticker", "side"], how="inner"
        ).with_columns(
            (
                (pl.col("model_win_probability") - pl.col("old_model_win_probability"))
                - (pl.col("entry_price_cents") - pl.col("old_entry_price_cents")) / 100
            ).mul(100).alias("residual_update_pp")
        )
        for threshold in dims["minimum_residual_updates_pp"]:
            for stat in dims["weather_stats"]:
                for side in dims["sides"]:
                    values = (f"{earlier}->{later}", f"update>={threshold}", stat, side)
                    registered.append(_registered_row("weather-revision-underreaction", values))
                    sub = paired.filter(
                        (pl.col("residual_update_pp") >= threshold)
                        & (pl.col("net_model_edge_cents") >= minimum_edge)
                        & (pl.col("weather_stat") == stat)
                        & (pl.col("side") == side)
                    )
                    frames.append(_cell(sub, "weather-revision-underreaction", [pl.lit(v) for v in values]))
    return pl.concat(frames, how="vertical_relaxed"), pl.DataFrame(registered)


def _combined_correction(cells: pl.DataFrame) -> pl.DataFrame:
    structural = (
        pl.read_parquet(MECHANISM_RESULTS)["search_p"].to_list()
        if MECHANISM_RESULTS.exists() else []
    )
    combined = structural + cells["search_p"].to_list()
    adjusted = false_discovery_adjust(combined)[len(structural):]
    return cells.with_columns(
        pl.Series("combined_suite_fdr_q", adjusted)
    ).with_columns(
        (
            pl.col("passes_all_folds")
            & (pl.col("family_fdr_q") <= 0.05)
            & (pl.col("combined_suite_fdr_q") <= 0.05)
        ).alias("historically_qualified")
    )


def _report(registry: dict, panel: pl.DataFrame, cells: pl.DataFrame) -> str:
    funnel = cells.select(
        pl.len().alias("registered"),
        pl.col("passes_all_folds").sum().alias("fold"),
        (pl.col("passes_all_folds") & (pl.col("family_fdr_q") <= 0.05)).sum().alias("family"),
        pl.col("historically_qualified").sum().alias("combined"),
    ).row(0, named=True)
    families = cells.group_by("family_id").agg(
        pl.len().alias("cells"),
        pl.col("passes_all_folds").sum().alias("fold"),
        (pl.col("passes_all_folds") & (pl.col("family_fdr_q") <= 0.05)).sum().alias("family"),
        pl.col("historically_qualified").sum().alias("qualified"),
    ).sort("family_id")
    brier = panel.filter(pl.col("side") == "yes").group_by(
        "decision_label"
    ).agg(
        pl.len().alias("rows"),
        ((pl.col("model_probability_yes") - pl.col("result_yes")) ** 2)
        .mean().alias("model_brier"),
        ((pl.col("yes_price_cents") / 100 - pl.col("result_yes")) ** 2)
        .mean().alias("market_brier"),
    ).sort("decision_label", descending=True)
    lines = [
        "# Weather external-alpha suite v1", "",
        f"Registry SHA-256: `{registry['sha256']}`", "",
        "This is a retrospective calibration test, not a historical fill claim. Forecasts "
        "are joined by conservative availability time; entries use last print plus a 2¢ "
        "spread reserve and taker fee. Every conditional rule must beat a matched market-only baseline.",
        "", "## Coverage", "",
        f"- Forecast-qualified strategy rows (YES and NO sides): **{panel.height:,}**",
        f"- Independent weather events: **{panel['event_ticker'].n_unique():,}**",
        f"- Settlement stations: **{panel['station'].n_unique():,}**",
        f"- Kalshi contracts: **{panel['ticker'].n_unique():,}**",
        "", "## Probability benchmark", "",
        "Lower Brier score is better. This is a diagnostic, not a trading return.", "",
        "| horizon | contract observations | GFS model | Kalshi price |",
        "|---|---:|---:|---:|",
    ]
    for row in brier.iter_rows(named=True):
        lines.append(
            f"| {row['decision_label']} | {row['rows']:,} | "
            f"{row['model_brier']:.6f} | {row['market_brier']:.6f} |"
        )
    lines += [
        "", "## Search funnel", "",
        "| stage | cells |", "|---|---:|",
        f"| registered external-data tests | {funnel['registered']:,} |",
        f"| passed all three folds | {funnel['fold']:,} |",
        f"| survived family FDR | {funnel['family']:,} |",
        f"| survived combined structural + external suite FDR | {funnel['combined']:,} |",
        "", "## Families", "",
        "| family | cells | fold passes | family FDR | final |", "|---|---:|---:|---:|---:|",
    ]
    for row in families.iter_rows(named=True):
        lines.append(
            f"| {row['family_id']} | {row['cells']} | {row['fold']} | "
            f"{row['family']} | {row['qualified']} |"
        )
    lines += ["", "## Best evidence per family", ""]
    for family in families["family_id"]:
        top = cells.filter(pl.col("family_id") == family).sort(
            "passes_all_folds", "combined_suite_fdr_q", "worst_annual_lower_bound",
            descending=[True, False, True], nulls_last=True,
        ).head(5)
        lines += [f"### {family}", "", "| cell | folds | min events | annual lower | hold lower | uplift lower | family q | combined q | fold pass | final |", "|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
        for row in top.iter_rows(named=True):
            def value(name: str) -> str:
                item = row[name]
                return "" if item is None else f"{item:.6f}"
            lines.append(
                f"| {row['cell_id']} | {row['n_periods']} | {row['minimum_fold_events']} | "
                f"{value('worst_annual_lower_bound')} | {value('worst_hold_lower_bound')} | "
                f"{value('worst_incremental_lower_bound')} | {row['family_fdr_q']:.6f} | "
                f"{row['combined_suite_fdr_q']:.6f} | {row['passes_all_folds']} | "
                f"{row['historically_qualified']} |"
            )
        lines.append("")
    lines += [
        "## Interpretation boundary", "",
        "The forecast archive is a third-party point extraction of NOAA GFS operational runs. "
        "NOAA NCEI Daily Summaries provide settlement-station observations for expanding error "
        "calibration. No current or future observation is allowed into a forecast probability. "
        "A historical survivor would still require live simultaneous books, forward shadow evidence, "
        "capacity, and operator approval.",
    ]
    return "\n".join(lines) + "\n"


def _funnel_svg(cells: pl.DataFrame, panel: pl.DataFrame) -> str:
    counts = [
        cells.height,
        cells.filter(pl.col("passes_all_folds")).height,
        cells.filter(pl.col("passes_all_folds") & (pl.col("family_fdr_q") <= 0.05)).height,
        cells.filter(pl.col("historically_qualified")).height,
    ]
    labels = ["Registered", "All folds", "Family FDR", "Combined FDR"]
    maximum = max(counts) or 1
    bars = []
    for index, (label, count) in enumerate(zip(labels, counts)):
        y = 60 + index * 62
        width = max(2, round(560 * count / maximum))
        bars.append(
            f'<text x="20" y="{y + 18}" font-size="15">{label}</text>'
            f'<rect x="145" y="{y}" width="{width}" height="28" rx="4" fill="#2563eb"/>'
            f'<text x="{155 + width}" y="{y + 19}" font-size="15">{count:,}</text>'
        )
    yes = panel.filter(pl.col("side") == "yes").group_by("decision_label").agg(
        ((pl.col("model_probability_yes") - pl.col("result_yes")) ** 2)
        .mean().alias("model"),
        ((pl.col("yes_price_cents") / 100 - pl.col("result_yes")) ** 2)
        .mean().alias("market"),
    ).sort("decision_label", descending=True)
    brier_bars = []
    for index, row in enumerate(yes.iter_rows(named=True)):
        y = 370 + index * 90
        for offset, key, color in ((0, "model", "#f59e0b"), (28, "market", "#2563eb")):
            width = round(2500 * row[key])
            brier_bars.append(
                f'<rect x="145" y="{y + offset}" width="{width}" height="20" rx="3" fill="{color}"/>'
                f'<text x="{155 + width}" y="{y + offset + 15}" font-size="13">{row[key]:.3f}</text>'
            )
        brier_bars.append(f'<text x="20" y="{y + 29}" font-size="15">{row["decision_label"]}</text>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="820" height="570" viewBox="0 0 820 570">'
        '<rect width="100%" height="100%" fill="white"/>'
        '<text x="20" y="32" font-size="21" font-weight="bold">Weather external-alpha search funnel</text>'
        + "".join(bars)
        + '<text x="20" y="338" font-size="21" font-weight="bold">Probability accuracy (Brier; lower is better)</text>'
        + '<rect x="500" y="324" width="16" height="16" fill="#f59e0b"/><text x="522" y="337" font-size="13">GFS model</text>'
        + '<rect x="610" y="324" width="16" height="16" fill="#2563eb"/><text x="632" y="337" font-size="13">Kalshi price</text>'
        + "".join(brier_bars) + '</svg>'
    )


def run() -> None:
    registry = _load_registry()
    panel = build_panel()
    frame, registered = build_family_frames(panel, registry)
    gate = registry["gate"]
    periods, cells = evaluate_registered_cells(
        frame, registered,
        minimum_events=gate["minimum_events_per_fold"],
        annual_hurdle=gate["annual_hurdle"],
        minimum_hold_return=gate["minimum_hold_return"],
        z=gate["error_multiplier"],
    )
    cells = _combined_correction(cells)
    float_periods = [name for name, dtype in periods.schema.items() if dtype in (pl.Float32, pl.Float64)]
    float_cells = [name for name, dtype in cells.schema.items() if dtype in (pl.Float32, pl.Float64)]
    periods = periods.with_columns(pl.col(float_periods).round(6))
    cells = cells.with_columns(pl.col(float_cells).round(6))
    WEATHER_PANEL.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(WEATHER_PANEL)
    periods.write_parquet(WEATHER_PERIODS)
    cells.write_parquet(WEATHER_RESULTS)
    REPORT_PATH.write_text(_report(registry, panel, cells))
    FUNNEL_PATH.write_text(_funnel_svg(cells, panel))
    print(
        f"weather alpha: {panel.height:,} strategy rows; {cells.height:,} cells; "
        f"{int(cells['historically_qualified'].sum())} qualified",
        flush=True,
    )


if __name__ == "__main__":
    run()
