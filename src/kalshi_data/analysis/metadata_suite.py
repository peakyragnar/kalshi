"""Metadata-dependent rule-language and threshold-ladder research."""

from __future__ import annotations

import re

import polars as pl

from .atlas import add_periods
from .mechanism_suite import (
    _markdown,
    add_side_economics,
    apply_search_correction,
    evaluate_cells,
    load_suite_registry,
    price_bucket,
    residualize_against_baseline,
)
from ..core.paths import (
    DECISION_POINTS,
    EVENT_COHERENCE,
    EVENT_COHERENCE_SUMMARY,
    LADDER_RESULTS,
    LADDER_SUMMARY,
    MARKET_METADATA,
    MARKETS,
    MECHANISM_PERIODS,
    MECHANISM_RESULTS,
    OUTCOMES,
    RESEARCH,
)


ABOVE_RE = re.compile(r"\b(or\s+above|at\s+least|above|greater\s+than|exceed(?:s|ed)?)\b", re.I)
BELOW_RE = re.compile(r"\b(or\s+below|at\s+most|below|less\s+than|under)\b", re.I)
JUDGMENT_RE = re.compile(
    r"\b(substantial(?:ly)?|significant(?:ly)?|credible|consensus|acknowledg(?:e|es|ed)|"
    r"attribut(?:e|es|ed|ion)|determined\s+by|according\s+to|deemed|considered)\b",
    re.I,
)
OFFICIAL_ACT_RE = re.compile(
    r"\b(signed\s+into\s+law|officially\s+(?:announc|confirm)|filed\s+with|published\s+by|"
    r"recorded\s+by|certified\s+by|sworn\s+in|takes?\s+office)\b",
    re.I,
)
NUMERIC_RE = re.compile(r"\b(value|price|rate|temperature|votes?|points?|percent|%|above|below)\b", re.I)


def infer_ladder_direction(subtitle: str | None, rules: str | None) -> str | None:
    for text in (subtitle, rules):
        if not text:
            continue
        above = bool(ABOVE_RE.search(text))
        below = bool(BELOW_RE.search(text))
        if above != below:
            return "above" if above else "below"
    return None


def ladder_strike(
    direction: str | None,
    floor_strike: float | None,
    cap_strike: float | None,
) -> float | None:
    """Return the threshold whose ordering determines an adjacent ladder."""
    if direction == "below" and cap_strike is not None:
        return cap_strike
    return floor_strike


def classify_rule(
    rules: str | None,
    floor_strike: float | None = None,
    cap_strike: float | None = None,
    expiration_value: str | float | None = None,
) -> str:
    text = rules or ""
    if JUDGMENT_RE.search(text):
        return "judgment_or_attribution"
    if OFFICIAL_ACT_RE.search(text):
        return "official_act"
    has_numeric_field = any(value is not None for value in (floor_strike, cap_strike))
    if expiration_value is not None:
        normalized_expiration = str(expiration_value).strip().lower()
        has_numeric_field = has_numeric_field or normalized_expiration not in {"", "yes", "no"}
    if has_numeric_field or (re.search(r"\d", text) and NUMERIC_RE.search(text)):
        return "numeric_objective"
    return "unclassified"


def build_ladder_pairs(frame: pl.DataFrame) -> pl.DataFrame:
    """Build adjacent strike comparisons and their signed monotonic gap."""
    keys = ["event_ticker", "decision_label", "decision_time", "direction"]
    ordered = frame.filter(
        pl.col("direction").is_in(["above", "below"])
        & pl.col("floor_strike").is_not_null()
    ).unique(keys + ["floor_strike"], keep="first").sort(keys + ["floor_strike"])
    paired = ordered.with_columns(
        pl.col("ticker").shift(1).over(keys).alias("lower_ticker"),
        pl.col("floor_strike").shift(1).over(keys).alias("lower_strike"),
        pl.col("yes_price_cents").shift(1).over(keys).alias("lower_yes_price_cents"),
        pl.col("trade_time").shift(1).over(keys).alias("lower_trade_time"),
    ).rename({
        "ticker": "higher_ticker",
        "floor_strike": "higher_strike",
        "yes_price_cents": "higher_yes_price_cents",
        "trade_time": "higher_trade_time",
    }).filter(pl.col("lower_ticker").is_not_null())
    paired = paired.with_columns(
        pl.when(pl.col("direction") == "above")
        .then(pl.col("higher_yes_price_cents") - pl.col("lower_yes_price_cents"))
        .otherwise(pl.col("lower_yes_price_cents") - pl.col("higher_yes_price_cents"))
        .alias("signed_gap_cents"),
        (
            pl.col("higher_trade_time") - pl.col("lower_trade_time")
        ).dt.total_seconds().abs().alias("trade_time_skew_seconds"),
    ).with_columns(
        (100 - pl.col("signed_gap_cents")).alias("pair_cost_cents"),
        (pl.col("signed_gap_cents") >= 2).alias("violation_2c"),
    ).with_columns(
        (pl.col("signed_gap_cents") / pl.col("pair_cost_cents")).alias("paired_return_proxy")
    )
    return paired


def build_event_coherence(frame: pl.DataFrame) -> pl.DataFrame:
    """Aggregate candidate-style exclusive event choices at each decision."""
    keys = ["event_ticker", "decision_label", "decision_time"]
    grouped = frame.filter(pl.col("is_exclusive_group")).group_by(keys).agg(
        pl.len().alias("contracts"),
        pl.col("expected_contracts").first().alias("expected_contracts"),
        pl.col("yes_price_cents").sum().alias("yes_price_sum_cents"),
        pl.col("trade_time").min().alias("earliest_trade_time"),
        pl.col("trade_time").max().alias("latest_trade_time"),
    ).filter(
        (pl.col("contracts") >= 2) & (pl.col("contracts") == pl.col("expected_contracts"))
    ).with_columns(
        (pl.col("yes_price_sum_cents") - 100).abs().alias("dislocation_cents"),
        pl.when(pl.col("yes_price_sum_cents") > 100)
        .then(pl.lit("buy_all_no"))
        .otherwise(pl.lit("buy_all_yes"))
        .alias("dislocation_side"),
        (pl.col("latest_trade_time") - pl.col("earliest_trade_time"))
        .dt.total_seconds().alias("trade_time_skew_seconds"),
    ).with_columns(
        pl.when(pl.col("dislocation_side") == "buy_all_no")
        .then(100 * pl.col("contracts") - pl.col("yes_price_sum_cents"))
        .otherwise(pl.col("yes_price_sum_cents"))
        .alias("multi_leg_cost_cents")
    ).with_columns(
        (pl.col("dislocation_cents") / pl.col("multi_leg_cost_cents"))
        .alias("multi_leg_return_proxy")
    )
    return grouped


def _metadata() -> pl.DataFrame:
    frame = pl.read_parquet(MARKET_METADATA / "*.parquet").unique("ticker", keep="first")
    return frame.with_columns(
        pl.col("floor_strike").cast(pl.Float64, strict=False),
        pl.col("cap_strike").cast(pl.Float64, strict=False),
        pl.col("settled_time").cast(pl.String).str.to_datetime(time_zone="UTC", strict=False),
    )


def _rule_frame(metadata: pl.DataFrame) -> pl.DataFrame:
    points = pl.read_parquet(DECISION_POINTS).filter(
        pl.col("decision_label").is_in(["T-7d", "T-30d", "T-90d"])
    )
    outcomes = pl.read_parquet(OUTCOMES).select(
        "ticker", "result_yes", "resolution_time", "resolution_time_trustworthy"
    )
    meta = metadata.join(points.select("ticker").unique(), on="ticker", how="inner").select(
        "ticker", "rules_primary", "floor_strike", "cap_strike", "expiration_value", "settled_time"
    ).with_columns(
        pl.struct("rules_primary", "floor_strike", "cap_strike", "expiration_value").map_elements(
            lambda row: classify_rule(
                row["rules_primary"], row["floor_strike"], row["cap_strike"], row["expiration_value"]
            ),
            return_dtype=pl.String,
        ).alias("rule_class")
    )
    base = add_periods(points.join(outcomes, on="ticker", how="inner").join(meta, on="ticker", how="inner"))
    base = base.with_columns(
        pl.when(pl.col("settled_time").is_not_null() & (pl.col("settled_time") > pl.col("decision_time")))
        .then((pl.col("settled_time") - pl.col("decision_time")).dt.total_seconds())
        .when(pl.col("resolution_time_trustworthy") & (pl.col("resolution_time") > pl.col("decision_time")))
        .then((pl.col("resolution_time") - pl.col("decision_time")).dt.total_seconds())
        .otherwise(pl.col("scheduled_hold_seconds"))
        .alias("hold_seconds")
    ).filter((pl.col("period") != "forward") & (pl.col("hold_seconds") > 0))
    base = add_side_economics(base).with_columns(
        pl.col("yes_price_cents").map_elements(price_bucket, return_dtype=pl.String).alias("price_bucket")
    ).filter(pl.col("price_bucket") != "out")
    base = residualize_against_baseline(
        base, ["category", "decision_label", "price_bucket", "side"]
    ).with_columns(
        pl.lit("rule-objectivity").alias("family_id"),
        pl.concat_str("rule_class", "decision_label", "price_bucket", "side", separator="|").alias("cell_id"),
    )
    return base.select(
        "family_id", "cell_id", "period", "event_ticker",
        "annualized_net_return", "incremental_return",
    )


def _ladder_frames(metadata: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    points = pl.read_parquet(DECISION_POINTS).filter(
        pl.col("decision_label").is_in(["T-1d", "T-7d", "T-30d"])
    )
    meta = metadata.join(points.select("ticker").unique(), on="ticker", how="inner").select(
        "ticker", "yes_sub_title", "rules_primary", "floor_strike", "cap_strike"
    ).with_columns(
        pl.struct("yes_sub_title", "rules_primary").map_elements(
            lambda row: infer_ladder_direction(row["yes_sub_title"], row["rules_primary"]),
            return_dtype=pl.String,
        ).alias("direction")
    ).with_columns(
        pl.struct("direction", "floor_strike", "cap_strike").map_elements(
            lambda row: ladder_strike(
                row["direction"], row["floor_strike"], row["cap_strike"]
            ),
            return_dtype=pl.Float64,
        ).alias("floor_strike")
    )
    pairs = add_periods(build_ladder_pairs(points.join(meta, on="ticker", how="inner"))).filter(
        pl.col("period") != "forward"
    )
    summary = pairs.group_by("direction", "decision_label", "period").agg(
        pl.len().alias("n_pairs"),
        pl.col("event_ticker").n_unique().alias("n_events"),
        pl.col("violation_2c").sum().alias("violations_2c"),
        pl.col("violation_2c").mean().alias("violation_rate"),
        pl.col("signed_gap_cents").mean().alias("mean_signed_gap_cents"),
        pl.col("signed_gap_cents").max().alias("max_signed_gap_cents"),
        (pl.col("trade_time_skew_seconds") <= 300).mean().alias("within_5m_share"),
        (pl.col("trade_time_skew_seconds") <= 300).sum().alias("within_5m_pairs"),
        ((pl.col("trade_time_skew_seconds") <= 300) & pl.col("violation_2c"))
        .sum().alias("within_5m_violations"),
    ).with_columns(
        pl.when(pl.col("within_5m_pairs") > 0)
        .then(pl.col("within_5m_violations") / pl.col("within_5m_pairs"))
        .otherwise(None).alias("within_5m_violation_rate")
    ).sort("direction", "decision_label", "period")
    return pairs, summary


def _coherence_frames(metadata: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    points = pl.read_parquet(DECISION_POINTS).filter(
        pl.col("decision_label").is_in(["T-1d", "T-7d", "T-30d"])
    )
    group_meta = metadata.join(
        points.select("event_ticker").unique(), on="event_ticker", how="inner"
    ).with_columns(
        pl.col("title").fill_null("").str.to_lowercase().alias("normalized_title"),
        pl.col("yes_sub_title").fill_null("").alias("choice_label"),
    ).group_by("event_ticker").agg(
        pl.len().alias("metadata_contracts"),
        pl.col("normalized_title").n_unique().alias("titles"),
        pl.col("choice_label").n_unique().alias("choices"),
        (pl.col("choice_label") == "").sum().alias("missing_choices"),
        (pl.col("floor_strike").is_not_null() | pl.col("cap_strike").is_not_null())
        .sum().alias("numeric_strikes"),
        pl.col("normalized_title").first().alias("normalized_title"),
    ).with_columns(
        (
            (pl.col("metadata_contracts") >= 2)
            & (pl.col("titles") == 1)
            & (pl.col("choices") == pl.col("metadata_contracts"))
            & (pl.col("missing_choices") == 0)
            & (pl.col("numeric_strikes") == 0)
            & pl.col("normalized_title").str.contains(
                r"(?i)(\bwho will (win|be (the )?.*nominee|become)\b|\bwhich (party|candidate)\b)"
            )
        ).alias("is_exclusive_group")
    ).select(
        "event_ticker", "is_exclusive_group",
        pl.col("metadata_contracts").alias("expected_contracts"),
    )
    coherence = add_periods(build_event_coherence(points.join(group_meta, on="event_ticker", how="inner"))).filter(
        pl.col("period") != "forward"
    )
    outcomes = pl.read_parquet(OUTCOMES).group_by("event_ticker").agg(
        pl.col("result_yes").sum().alias("settled_yes_count")
    )
    coherence = coherence.join(outcomes, on="event_ticker", how="left").with_columns(
        (pl.col("settled_yes_count") == 1).alias("outcome_structure_valid")
    )
    summary = coherence.group_by("decision_label", "period").agg(
        pl.len().alias("events"),
        (pl.col("dislocation_cents") >= 2).sum().alias("dislocations_2c"),
        (pl.col("dislocation_cents") >= 2).mean().alias("dislocation_rate"),
        pl.col("dislocation_cents").mean().alias("mean_dislocation_cents"),
        pl.col("dislocation_cents").max().alias("max_dislocation_cents"),
        (pl.col("trade_time_skew_seconds") <= 300).mean().alias("within_5m_share"),
        pl.col("outcome_structure_valid").mean().alias("classification_precision"),
    ).sort("decision_label", "period")
    return coherence, summary


def _report(
    cells: pl.DataFrame, summary: pl.DataFrame, coherence_summary: pl.DataFrame,
    metadata: pl.DataFrame, canonical_markets: int, canonical_covered: int,
) -> str:
    rule = cells.filter(pl.col("family_id") == "rule-objectivity")
    lines = [
        "# Metadata-dependent mechanism results", "",
        f"Canonical historical metadata coverage: **{canonical_covered:,} / {canonical_markets:,} markets**. "
        f"The API returned **{metadata['ticker'].n_unique() - canonical_covered:,}** additional settled tickers, "
        "which are retained but do not enter the canonical universe without a join.", "",
        "## Rule-language mechanism", "",
        f"Tested **{len(rule):,}** rule-class cells; **{int(rule['historically_qualified'].sum()):,}** "
        "survived three folds, event support, economic gates, matched-baseline uplift, family FDR, and suite FDR.", "",
        "## Threshold-ladder dislocations", "",
        "These are asynchronous last-trade calibration comparisons, not executable arbitrages. A live candidate "
        "still requires both legs to be offered simultaneously at the observed prices.", "",
        "| direction | horizon | fold | pairs | events | gaps >=2c | rate | mean signed gap | within 5m | sync gap rate |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.iter_rows(named=True):
        sync_rate = row["within_5m_violation_rate"]
        sync_rate_text = "n/a" if sync_rate is None else f"{sync_rate:.2%}"
        lines.append(
            f"| {row['direction']} | {row['decision_label']} | {row['period']} | {row['n_pairs']:,} | "
            f"{row['n_events']:,} | {row['violations_2c']:,} | {row['violation_rate']:.2%} | "
            f"{row['mean_signed_gap_cents']:.3f}c | {row['within_5m_share']:.2%} | "
            f"{sync_rate_text} |"
        )
    lines += [
        "", "## Mutually exclusive event price sums", "",
        "Candidate-style groups are identified from shared titles and distinct non-numeric choice labels. "
        "Final outcomes validate classification only; they are not used as a decision-time feature. Like ladders, "
        "the historical prices are asynchronous and do not prove all legs were executable together.", "",
        "| horizon | fold | events | gaps >=2c | rate | mean gap | within 5m | exact-one outcome |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in coherence_summary.iter_rows(named=True):
        lines.append(
            f"| {row['decision_label']} | {row['period']} | {row['events']:,} | "
            f"{row['dislocations_2c']:,} | {row['dislocation_rate']:.2%} | "
            f"{row['mean_dislocation_cents']:.3f}c | {row['within_5m_share']:.2%} | "
            f"{row['classification_precision']:.2%} |"
        )
    return "\n".join(lines) + "\n"


def run() -> None:
    registry = load_suite_registry(RESEARCH / "mechanism-suite-v1.yaml")
    contract = registry["common_contract"]
    metadata = _metadata()
    rule_periods, rule_cells = evaluate_cells(
        _rule_frame(metadata),
        contract["minimum_events_per_fold"],
        contract["economic_hurdle"],
        contract["error_multiplier"],
        require_incremental=True,
    )
    base_cells = pl.read_parquet(MECHANISM_RESULTS).select(
        "family_id", "cell_id", "n_periods", "all_observed_periods_pass", "worst_period_p",
        "worst_lower_bound", "worst_incremental_lower_bound", "minimum_fold_events", "n_total",
        "passes_all_folds",
    ).filter(pl.col("family_id") != "rule-objectivity")
    cells = apply_search_correction(
        pl.concat([base_cells, rule_cells], how="vertical_relaxed"),
        contract["minimum_events_per_fold"],
    )
    base_periods = pl.read_parquet(MECHANISM_PERIODS).select(
        "family_id", "cell_id", "period", "n", "n_events", "mean_ann_net", "cluster_se",
        "mean_incremental", "incremental_se", "incremental_lower_bound", "lower_bound",
        "p_value", "period_pass",
    ).filter(pl.col("family_id") != "rule-objectivity")
    periods = pl.concat([base_periods, rule_periods], how="vertical_relaxed").join(
        cells.select("family_id", "cell_id", "family_fdr_q", "suite_fdr_q", "historically_qualified"),
        on=["family_id", "cell_id"], how="left",
    )
    float_cells = [name for name, dtype in cells.schema.items() if dtype in (pl.Float32, pl.Float64)]
    float_periods = [name for name, dtype in periods.schema.items() if dtype in (pl.Float32, pl.Float64)]
    cells.with_columns(pl.col(float_cells).round(6)).write_parquet(MECHANISM_RESULTS)
    periods.with_columns(pl.col(float_periods).round(6)).write_parquet(MECHANISM_PERIODS)
    (RESEARCH / "mechanism-suite.md").write_text(_markdown(registry, cells, periods))
    pairs, summary = _ladder_frames(metadata)
    pairs.write_parquet(LADDER_RESULTS)
    summary.write_parquet(LADDER_SUMMARY)
    coherence, coherence_summary = _coherence_frames(metadata)
    coherence.write_parquet(EVENT_COHERENCE)
    coherence_summary.write_parquet(EVENT_COHERENCE_SUMMARY)
    canonical = pl.scan_parquet(MARKETS / "*.parquet").select("ticker").unique().collect()
    canonical_covered = canonical.join(
        metadata.select("ticker").unique(), on="ticker", how="inner"
    )["ticker"].n_unique()
    (RESEARCH / "metadata-suite.md").write_text(
        _report(cells, summary, coherence_summary, metadata, len(canonical), canonical_covered)
    )
    print(
        f"metadata suite: {len(rule_cells):,} rule cells; {len(pairs):,} adjacent ladder pairs; "
        f"{len(coherence):,} exclusive-event observations; "
        f"{int(cells['historically_qualified'].sum())} suite survivors",
        flush=True,
    )


if __name__ == "__main__":
    run()
