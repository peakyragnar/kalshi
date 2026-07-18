"""Registered multi-mechanism alpha search over the canonical decision panel."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlparse

import polars as pl

from .atlas import add_periods, false_discovery_adjust
from .screen_d import load as load_fills
from .screens import cell_stats
from ..core.paths import (
    DECISION_POINTS,
    MARKET_RELATIONS,
    MECHANISM_PERIODS,
    MECHANISM_RESULTS,
    OUTCOMES,
    RESEARCH,
    SERIES,
)


CARRY_APY = 0.0325
FOLDS = ("early", "middle", "recent")
PRICE_BUCKETS = ((1, 5), (6, 10), (11, 20), (21, 40), (41, 60), (61, 80), (81, 95), (96, 99))


def load_suite_registry(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        registry = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"suite registry must be deterministic JSON-compatible YAML: {exc}") from exc
    if registry.get("version") != 1 or not isinstance(registry.get("families"), list):
        raise ValueError("suite registry requires version=1 and families")
    common = registry.get("common_contract") or {}
    for field in (
        "minimum_events_per_fold", "economic_hurdle", "error_multiplier",
        "cluster_by", "folds", "search_control", "sealed_forward_start",
    ):
        if field not in common:
            raise ValueError(f"suite common contract missing {field}")
    ids = [family.get("id") for family in registry["families"]]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError("suite family ids must be present and unique")
    registry["sha256"] = hashlib.sha256(raw).hexdigest()
    return registry


def price_bucket(price: int) -> str:
    for lo, hi in PRICE_BUCKETS:
        if lo <= price <= hi:
            return f"{lo:02d}-{hi:02d}"
    return "out"


def _price_bucket_expr(column: str = "yes_price_cents") -> pl.Expr:
    p = pl.col(column)
    out = pl.lit("out")
    for lo, hi in reversed(PRICE_BUCKETS):
        out = pl.when(p.is_between(lo, hi)).then(pl.lit(f"{lo:02d}-{hi:02d}")).otherwise(out)
    return out.alias("price_bucket")


def add_side_economics(frame: pl.DataFrame) -> pl.DataFrame:
    """Duplicate observable decisions into fixed YES and NO settlement economics."""
    p = pl.col("yes_price_cents").cast(pl.Float64)
    fee = pl.when(pl.col("fee_type") == "quadratic_with_maker_fees").then(
        ((7 * p * (100 - p) + 39999) // 40000).cast(pl.Float64)
    ).otherwise(0.0)
    y = pl.col("result_yes").cast(pl.Float64)
    yes = frame.with_columns(pl.lit("yes").alias("side")).with_columns(
        ((100 * y - p - fee) / p).alias("hold_return")
    )
    q = 100 - p
    no = frame.with_columns(pl.lit("no").alias("side")).with_columns(
        ((100 * (1 - y) - q - fee) / q).alias("hold_return")
    )
    return pl.concat([yes, no], how="vertical_relaxed").with_columns(
        (
            pl.col("hold_return") * (365 * 86400) / pl.col("hold_seconds")
            + CARRY_APY
        ).alias("annualized_net_return")
    )


def build_path_rows(points: pl.DataFrame, pairs: list[tuple[str, str]]) -> pl.DataFrame:
    frames = []
    for earlier_label, later_label in pairs:
        prior = points.filter(pl.col("decision_label") == earlier_label).select(
            "ticker",
            pl.col("decision_time").alias("prior_decision_time"),
            pl.col("yes_price_cents").alias("prior_yes_price_cents"),
        )
        later = points.filter(pl.col("decision_label") == later_label)
        paired = later.join(prior, on="ticker", how="inner").filter(
            pl.col("prior_decision_time") < pl.col("decision_time")
        ).with_columns(
            (pl.col("yes_price_cents") - pl.col("prior_yes_price_cents")).alias("price_move_cents"),
            pl.lit(f"{earlier_label}->{later_label}").alias("path_pair"),
        )
        frames.append(paired)
    return pl.concat(frames, how="diagonal_relaxed") if frames else points.head(0)


def _p_value(mean: float, se: float, hurdle: float) -> float:
    if not math.isfinite(mean) or not math.isfinite(se):
        return 1.0
    if se == 0:
        return 0.0 if mean > hurdle else 1.0
    return 0.5 * math.erfc(((mean - hurdle) / se) / math.sqrt(2))


def evaluate_cells(
    frame: pl.DataFrame, minimum_events: int, hurdle: float, z: float
) -> tuple[pl.DataFrame, pl.DataFrame]:
    required = {"family_id", "cell_id", "period", "event_ticker", "annualized_net_return"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"cell frame missing {', '.join(sorted(missing))}")
    stats = cell_stats(
        frame.filter(pl.col("period").is_in(FOLDS)),
        ["family_id", "cell_id", "period"],
        "annualized_net_return",
    ).rename({
        "annualized_net_return_mean": "mean_ann_net",
        "annualized_net_return_se": "cluster_se",
    }).with_columns(
        (pl.col("mean_ann_net") - z * pl.col("cluster_se")).alias("lower_bound")
    ).with_columns(
        pl.struct("mean_ann_net", "cluster_se").map_elements(
            lambda row: _p_value(row["mean_ann_net"], row["cluster_se"], hurdle),
            return_dtype=pl.Float64,
        ).alias("p_value"),
        ((pl.col("n_events") >= minimum_events) & (pl.col("lower_bound") > hurdle)).alias("period_pass"),
    )
    cells = stats.group_by("family_id", "cell_id").agg(
        pl.col("period").n_unique().alias("n_periods"),
        pl.col("period_pass").all().alias("all_observed_periods_pass"),
        pl.col("p_value").max().alias("worst_period_p"),
        pl.col("lower_bound").min().alias("worst_lower_bound"),
        pl.col("n_events").min().alias("minimum_fold_events"),
        pl.col("n").sum().alias("n_total"),
    ).with_columns(
        ((pl.col("n_periods") == len(FOLDS)) & pl.col("all_observed_periods_pass")).alias("passes_all_folds")
    ).sort("family_id", "cell_id")
    return stats.sort("family_id", "cell_id", "period"), cells


def classify_settlement_source(raw: str | None) -> str:
    if not raw:
        return "missing"
    try:
        sources = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        sources = []
    if not sources:
        return "missing"
    hosts = [urlparse(str(source.get("url") or "")).hostname or "" for source in sources]
    if any(host.endswith(".gov") or host in {"gov.uk", "parliament.uk"} for host in hosts):
        return "government"
    exchange_tokens = ("nasdaq", "nyse", "cmegroup", "tradingview", "google.com", "fred.stlouisfed", "bls")
    if any(any(token in host for token in exchange_tokens) for host in hosts):
        return "exchange_or_data"
    return "media_or_other"


def _fixed_bin(column: str, bins: list[list[float]], name: str) -> pl.Expr:
    value = pl.col(column)
    out = pl.lit("out")
    for lo, hi in reversed(bins):
        label = f"{lo:g}:{hi:g}"
        out = pl.when((value >= lo) & (value < hi)).then(pl.lit(label)).otherwise(out)
    return out.alias(name)


def _cellize(frame: pl.DataFrame, family_id: str, dimensions: list[str]) -> pl.DataFrame:
    return frame.with_columns(
        pl.lit(family_id).alias("family_id"),
        pl.concat_str([pl.col(column).cast(pl.String) for column in dimensions], separator="|").alias("cell_id"),
    ).select("family_id", "cell_id", "period", "event_ticker", "annualized_net_return")


def _base_panel() -> pl.DataFrame:
    points = pl.read_parquet(DECISION_POINTS)
    outcomes = pl.read_parquet(OUTCOMES).select("ticker", "result_yes")
    return add_periods(points.join(outcomes, on="ticker", how="inner")).with_columns(
        pl.col("scheduled_hold_seconds").alias("hold_seconds"),
        _price_bucket_expr(),
    ).filter(
        pl.col("decision_time_trustworthy")
        & pl.col("yes_price_cents").is_between(1, 99)
        & (pl.col("hold_seconds") > 0)
        & (pl.col("period") != "forward")
        & ~pl.col("is_block_trade").fill_null(False)
    )


def build_registered_family_frames(base: pl.DataFrame, registry: dict) -> dict[str, pl.DataFrame]:
    specs = {family["id"]: family for family in registry["families"]}
    frames: dict[str, pl.DataFrame] = {}

    close = base.filter(
        pl.col("decision_label").is_in(specs["two-sided-close-calibration"]["dimensions"]["decision_labels"])
        & (pl.col("price_staleness_seconds") <= 0.2 * pl.col("scheduled_hold_seconds"))
    )
    frames["two-sided-close-calibration"] = _cellize(
        add_side_economics(close), "two-sided-close-calibration",
        ["category", "decision_label", "price_bucket", "side"],
    )

    listing_spec = specs["listing-lifecycle"]["dimensions"]
    listing = base.filter(
        pl.col("decision_label").is_in(listing_spec["decision_labels"])
        & (pl.col("price_staleness_seconds") <= listing_spec["maximum_staleness_as_listing_age"] * pl.col("listing_age_seconds"))
    )
    frames["listing-lifecycle"] = _cellize(
        add_side_economics(listing), "listing-lifecycle",
        ["category", "decision_label", "price_bucket", "side"],
    )

    path_spec = specs["price-path-dependence"]["dimensions"]
    paths = build_path_rows(base, [tuple(pair) for pair in path_spec["label_pairs"]]).with_columns(
        _fixed_bin("price_move_cents", path_spec["move_bins_cents"], "move_bin")
    ).filter(pl.col("move_bin") != "out")
    frames["price-path-dependence"] = _cellize(
        add_side_economics(paths), "price-path-dependence",
        ["path_pair", "move_bin", "price_bucket", "side"],
    )

    flow_spec = specs["aggressor-imbalance"]["dimensions"]
    flow = base.filter(
        pl.col("decision_label").is_in(flow_spec["decision_labels"])
        & (pl.col("volume_24h") >= flow_spec["minimum_24h_volume"])
        & pl.col("yes_taker_share_24h").is_not_null()
    ).with_columns(_fixed_bin("yes_taker_share_24h", flow_spec["yes_taker_share_bins"], "flow_bin"))
    frames["aggressor-imbalance"] = _cellize(
        add_side_economics(flow), "aggressor-imbalance",
        ["decision_label", "flow_bin", "price_bucket", "side"],
    )

    activity_spec = specs["recent-activity"]["dimensions"]
    activity = base.filter(pl.col("decision_label").is_in(activity_spec["decision_labels"])).with_columns(
        _fixed_bin("volume_24h", activity_spec["volume_24h_bins"], "activity_bin")
    )
    frames["recent-activity"] = _cellize(
        add_side_economics(activity), "recent-activity",
        ["decision_label", "activity_bin", "price_bucket", "side"],
    )

    stale_spec = specs["price-staleness"]["dimensions"]
    stale = base.filter(pl.col("decision_label").is_in(stale_spec["decision_labels"])).with_columns(
        (pl.col("price_staleness_seconds") / pl.col("scheduled_hold_seconds")).alias("staleness_fraction")
    ).with_columns(_fixed_bin("staleness_fraction", stale_spec["staleness_fraction_bins"], "staleness_bin")).filter(
        pl.col("staleness_bin") != "out"
    )
    frames["price-staleness"] = _cellize(
        add_side_economics(stale), "price-staleness",
        ["decision_label", "staleness_bin", "price_bucket", "side"],
    )

    series_spec = specs["recurring-series-residual"]["dimensions"]
    series = base.filter(pl.col("decision_label").is_in(series_spec["decision_labels"]))
    frames["recurring-series-residual"] = _cellize(
        add_side_economics(series), "recurring-series-residual",
        ["series_ticker", "decision_label", "price_bucket", "side"],
    )

    month_spec = specs["calendar-month"]["dimensions"]
    month = base.filter(pl.col("decision_label").is_in(month_spec["decision_labels"])).with_columns(
        pl.col("decision_time").dt.month().alias("calendar_value")
    )
    frames["calendar-month"] = _cellize(
        add_side_economics(month), "calendar-month",
        ["decision_label", "calendar_value", "price_bucket", "side"],
    )

    weekday_spec = specs["calendar-weekday"]["dimensions"]
    weekday = base.filter(pl.col("decision_label").is_in(weekday_spec["decision_labels"])).with_columns(
        pl.col("decision_time").dt.weekday().alias("calendar_value")
    )
    frames["calendar-weekday"] = _cellize(
        add_side_economics(weekday), "calendar-weekday",
        ["decision_label", "calendar_value", "price_bucket", "side"],
    )

    early_spec = specs["early-close-risk"]["dimensions"]
    early = base.filter(pl.col("decision_label").is_in(early_spec["decision_labels"]))
    frames["early-close-risk"] = _cellize(
        add_side_economics(early), "early-close-risk",
        ["decision_label", "can_close_early", "price_bucket", "side"],
    )

    relations = pl.read_parquet(MARKET_RELATIONS).select("ticker", "event_group_size")
    event_spec = specs["event-structure"]["dimensions"]
    event = base.filter(pl.col("decision_label").is_in(event_spec["decision_labels"])).join(
        relations, on="ticker", how="inner"
    ).with_columns(_fixed_bin("event_group_size", event_spec["event_group_size_bins"], "event_size_bin"))
    frames["event-structure"] = _cellize(
        add_side_economics(event), "event-structure",
        ["decision_label", "event_size_bin", "price_bucket", "side"],
    )

    source_classes = pl.read_parquet(SERIES).select("ticker", "settlement_sources").with_columns(
        pl.col("settlement_sources").map_elements(classify_settlement_source, return_dtype=pl.String).alias("source_class")
    ).rename({"ticker": "series_ticker"}).select("series_ticker", "source_class")
    source_spec = specs["settlement-source"]["dimensions"]
    source = base.filter(pl.col("decision_label").is_in(source_spec["decision_labels"])).join(
        source_classes, on="series_ticker", how="left"
    ).with_columns(pl.col("source_class").fill_null("missing"))
    frames["settlement-source"] = _cellize(
        add_side_economics(source), "settlement-source",
        ["decision_label", "source_class", "price_bucket", "side"],
    )
    return frames


def _maker_frame() -> pl.DataFrame:
    fills = add_periods(load_fills().rename({"created_time": "decision_time"})).with_columns(
        pl.when(pl.col("taker_side") == "yes").then(pl.lit("no")).otherwise(pl.lit("yes")).alias("maker_side"),
        (pl.col("ret_maker") * 365 / pl.col("horizon_days") + CARRY_APY).alias("annualized_net_return"),
    ).with_columns(
        pl.col("hbucket").str.replace("a ", "").str.replace("b ", "").str.replace("c ", "").str.replace("d ", "").str.replace("e ", "").alias("horizon_bin"),
        pl.lit("conditional-maker-selection").alias("family_id"),
    ).with_columns(
        pl.concat_str("category", "horizon_bin", "bucket", "maker_side", separator="|").alias("cell_id")
    )
    return fills.select("family_id", "cell_id", "period", "event_ticker", "annualized_net_return")


def _apply_fdr(cells: pl.DataFrame) -> pl.DataFrame:
    pieces = []
    for _, family in cells.partition_by("family_id", as_dict=True).items():
        q = false_discovery_adjust(family["worst_period_p"].to_list())
        pieces.append(family.with_columns(pl.Series("family_fdr_q", q)))
    out = pl.concat(pieces).sort("family_id", "cell_id")
    global_q = false_discovery_adjust(out["worst_period_p"].to_list())
    return out.with_columns(pl.Series("suite_fdr_q", global_q)).with_columns(
        (
            pl.col("passes_all_folds")
            & (pl.col("family_fdr_q") <= 0.05)
            & (pl.col("suite_fdr_q") <= 0.05)
        ).alias("historically_qualified")
    )


def _markdown(registry: dict, cells: pl.DataFrame, periods: pl.DataFrame) -> str:
    family_rows = cells.group_by("family_id").agg(
        pl.len().alias("cells"),
        pl.col("passes_all_folds").sum().alias("fold_survivors"),
        (pl.col("passes_all_folds") & (pl.col("family_fdr_q") <= 0.05)).sum().alias("family_fdr_survivors"),
        pl.col("historically_qualified").sum().alias("suite_survivors"),
    ).sort("family_id")
    lines = [
        "# Multi-mechanism alpha suite v1", "",
        f"Registry SHA-256: `{registry['sha256']}`", "",
        "Every result is retrospective. Qualification requires three chronological folds, "
        "50 independent events per fold, mean minus two clustered standard errors above "
        "7%, family FDR, and suite-wide FDR. Historical qualification is not deployment.", "",
        "## Search funnel by mechanism", "",
        "| family | cells | fold survivors | family-FDR survivors | suite survivors |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in family_rows.iter_rows(named=True):
        lines.append(
            f"| {row['family_id']} | {row['cells']} | {row['fold_survivors']} | "
            f"{row['family_fdr_survivors']} | {row['suite_survivors']} |"
        )
    lines += ["", "## Best surviving evidence per family", ""]
    for family_id in family_rows["family_id"]:
        top = cells.filter(pl.col("family_id") == family_id).sort(
            "passes_all_folds", "suite_fdr_q", "worst_lower_bound",
            descending=[True, False, True],
        ).head(5)
        lines += [f"### {family_id}", "", "| cell | folds pass | min events | worst lower | family q | suite q |", "|---|---:|---:|---:|---:|---:|"]
        for row in top.iter_rows(named=True):
            lines.append(
                f"| {row['cell_id']} | {row['passes_all_folds']} | {row['minimum_fold_events']} | "
                f"{row['worst_lower_bound']:.4f} | {row['family_fdr_q']:.6f} | {row['suite_fdr_q']:.6f} |"
            )
        lines.append("")
    lines += [
        "## Metadata-dependent registered tests", "",
        "Ladder monotonicity and rule-objectivity remain registered but are reported by the "
        "metadata suite after historical titles, strikes, and rules are backfilled.", "",
        f"Full machine-readable evidence: `{MECHANISM_RESULTS.relative_to(MECHANISM_RESULTS.parents[2])}` "
        f"and `{MECHANISM_PERIODS.relative_to(MECHANISM_PERIODS.parents[2])}`.",
    ]
    return "\n".join(lines) + "\n"


def run() -> None:
    registry_path = RESEARCH / "mechanism-suite-v1.yaml"
    registry = load_suite_registry(registry_path)
    contract = registry["common_contract"]
    base = _base_panel()
    frames = build_registered_family_frames(base, registry)
    period_parts, cell_parts = [], []
    for family_id, frame in frames.items():
        periods, cells = evaluate_cells(
            frame,
            contract["minimum_events_per_fold"],
            contract["economic_hurdle"],
            contract["error_multiplier"],
        )
        period_parts.append(periods)
        cell_parts.append(cells)
        print(f"{family_id}: {len(cells):,} cells", flush=True)
    maker_periods, maker_cells = evaluate_cells(
        _maker_frame(),
        contract["minimum_events_per_fold"],
        contract["economic_hurdle"],
        contract["error_multiplier"],
    )
    period_parts.append(maker_periods)
    cell_parts.append(maker_cells)
    periods = pl.concat(period_parts, how="vertical_relaxed")
    cells = _apply_fdr(pl.concat(cell_parts, how="vertical_relaxed"))
    period_float_columns = [name for name, dtype in periods.schema.items() if dtype in (pl.Float32, pl.Float64)]
    cell_float_columns = [name for name, dtype in cells.schema.items() if dtype in (pl.Float32, pl.Float64)]
    periods = periods.with_columns(pl.col(period_float_columns).round(6))
    cells = cells.with_columns(pl.col(cell_float_columns).round(6))
    MECHANISM_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    cells.write_parquet(MECHANISM_RESULTS)
    periods.join(
        cells.select("family_id", "cell_id", "family_fdr_q", "suite_fdr_q", "historically_qualified"),
        on=["family_id", "cell_id"], how="left",
    ).write_parquet(MECHANISM_PERIODS)
    (RESEARCH / "mechanism-suite.md").write_text(_markdown(registry, cells, periods))
    print(
        f"mechanism suite: {len(cells):,} cells; "
        f"{int(cells['historically_qualified'].sum())} historically qualified",
        flush=True,
    )


if __name__ == "__main__":
    run()
