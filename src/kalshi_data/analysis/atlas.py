"""Deterministic runner for pre-registered structural hypotheses."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import polars as pl

from .registry import load_registry
from .screens import cluster_se
from ..core.paths import ATLAS_RESULTS, DECISION_POINTS, OUTCOMES, RESEARCH


CARRY_APY = 0.0325
SEALED_FORWARD_START = dt.datetime(2026, 7, 17, tzinfo=dt.timezone.utc)


def false_discovery_adjust(p_values: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values in original order."""
    m = len(p_values)
    if not m:
        return []
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [1.0] * m
    running = 1.0
    for rank_index in range(m - 1, -1, -1):
        original = order[rank_index]
        rank = rank_index + 1
        running = min(running, p_values[original] * m / rank)
        adjusted[original] = min(1.0, running)
    return adjusted


def add_periods(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.when(pl.col("decision_time") < pl.lit(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)))
        .then(pl.lit("early"))
        .when(pl.col("decision_time") < pl.lit(dt.datetime(2025, 7, 1, tzinfo=dt.timezone.utc)))
        .then(pl.lit("middle"))
        .when(pl.col("decision_time") < pl.lit(SEALED_FORWARD_START))
        .then(pl.lit("recent"))
        .otherwise(pl.lit("forward")).alias("period")
    )


def _filter(df: pl.DataFrame, filters: dict) -> pl.DataFrame:
    out = df
    if filters.get("categories"):
        out = out.filter(pl.col("category").is_in(filters["categories"]))
    if filters.get("decision_labels"):
        out = out.filter(pl.col("decision_label").is_in(filters["decision_labels"]))
    if filters.get("series"):
        out = out.filter(pl.col("series_ticker").is_in(filters["series"]))
    if filters.get("exclude_series"):
        out = out.filter(~pl.col("series_ticker").is_in(filters["exclude_series"]))
    if "yes_price_min" in filters:
        out = out.filter(pl.col("yes_price_cents") >= filters["yes_price_min"])
    if "yes_price_max" in filters:
        out = out.filter(pl.col("yes_price_cents") <= filters["yes_price_max"])
    if "max_staleness_fraction" in filters:
        out = out.filter(
            pl.col("price_staleness_seconds")
            <= pl.col("scheduled_hold_seconds") * filters["max_staleness_fraction"]
        )
    return out.filter(pl.col("decision_time_trustworthy"))


def expand_hypotheses(registry: dict) -> list[dict]:
    """Expand only dimensions declared in the sealed registry."""
    expanded = []
    for spec in registry["hypotheses"]:
        if spec["kind"] != "cell_grid_no_maker":
            expanded.append(spec)
            continue
        dims = spec["dimensions"]
        for category in dims["categories"]:
            for label in dims["decision_labels"]:
                for lo, hi in dims["price_buckets"]:
                    child = {**spec}
                    child["kind"] = "cell_no_maker"
                    child["id"] = (
                        f"{spec['id']}__{category.lower().replace(' ', '-')}__"
                        f"{label.lower()}__{lo:02d}-{hi:02d}"
                    )
                    child["filters"] = {
                        **spec.get("filters", {}),
                        "categories": [category],
                        "decision_labels": [label],
                        "yes_price_min": lo,
                        "yes_price_max": hi,
                    }
                    child["parent_id"] = spec["id"]
                    expanded.append(child)
    return expanded


def _no_maker_returns(df: pl.DataFrame) -> pl.DataFrame:
    p = pl.col("yes_price_cents")
    q = 100 - p
    fee = pl.when(pl.col("fee_type") == "quadratic_with_maker_fees").then(
        (7 * p * (100 - p) + 39999) // 40000
    ).otherwise(0)
    hold = pl.col("hold_seconds").cast(pl.Float64)
    hold_ret = (100 * (1 - pl.col("result_yes")) - q - fee) / q
    return df.with_columns(hold_ret.alias("hold_return")).with_columns(
        (pl.col("hold_return") * (365 * 86400) / hold + CARRY_APY).alias("annualized_net_return")
    )


def evaluate_hypothesis(df: pl.DataFrame, spec: dict) -> tuple[dict, list[dict]]:
    sub = _no_maker_returns(_filter(df, spec.get("filters", {})))
    gate = spec["gate"]
    rows = []
    for period in ("early", "middle", "recent"):
        cell = sub.filter(pl.col("period") == period)
        n_events = cell["event_ticker"].n_unique() if len(cell) else 0
        mean = float(cell["annualized_net_return"].mean()) if len(cell) else float("nan")
        se = cluster_se(cell["annualized_net_return"], cell["event_ticker"]) if len(cell) else float("nan")
        mean_hold = float(cell["hold_return"].mean()) if len(cell) else float("nan")
        se_hold = cluster_se(cell["hold_return"], cell["event_ticker"]) if len(cell) else float("nan")
        lower = mean - gate["z"] * se if math.isfinite(mean) and math.isfinite(se) else float("nan")
        z_score = (mean - gate["hurdle"]) / se if se and math.isfinite(se) else (math.inf if mean > gate["hurdle"] else -math.inf)
        p_value = 0.5 * math.erfc(z_score / math.sqrt(2)) if math.isfinite(z_score) else (0.0 if z_score > 0 else 1.0)
        event_counts = cell.group_by("event_ticker").len().sort("len", descending=True) if len(cell) else None
        top10_share = float(event_counts.head(10)["len"].sum() / len(cell)) if len(cell) else float("nan")
        rows.append({
            "hypothesis_id": spec["id"], "period": period, "n": len(cell),
            "n_events": n_events, "mean_ann_net": mean, "cluster_se": se,
            "mean_hold_return": mean_hold, "hold_return_se": se_hold,
            "lower_bound": lower, "p_value": p_value, "top10_event_share": top10_share,
            "tail_loss_rate": float((cell["hold_return"] < 0).mean()) if len(cell) else float("nan"),
            "period_pass": n_events >= gate["minimum_events"] and lower > gate["hurdle"],
        })
    qualified = all(r["period_pass"] for r in rows)
    insufficient = [r["period"] for r in rows if r["n_events"] < gate["minimum_events"]]
    economic_failures = [
        r["period"] for r in rows
        if math.isfinite(r["lower_bound"]) and r["lower_bound"] <= gate["hurdle"]
    ]
    result = {
        "hypothesis_id": spec["id"],
        "historically_qualified": qualified,
        "searched_status": spec.get("status"),
        "retroactive": spec.get("retroactive", False),
        "worst_period_p": max(r["p_value"] for r in rows),
        "insufficient_periods": ",".join(insufficient),
        "economic_failure_periods": ",".join(economic_failures),
    }
    return result, rows


def _manifest_hash(paths: list[Path]) -> str:
    """Fingerprint the input bytes, not merely their filenames and sizes."""
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(path.name.encode())
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                h.update(chunk)
    return h.hexdigest()


def _markdown(registry: dict, results: list[dict], periods: list[dict], input_hash: str) -> str:
    by_id = {r["hypothesis_id"]: r for r in results}
    pre_fdr = [r for r in results if r["passes_all_folds_pre_fdr"]]
    qualified = [r for r in results if r["historically_qualified"]]
    lines = [
        "# Structural edge atlas", "",
        f"Registry SHA-256: `{registry['sha256']}`",
        f"Input manifest SHA-256: `{input_hash}`", "",
        "Historical periods are robustness folds, not untouched holdouts. Outcomes from "
        "2026-07-17 onward are the sealed forward period. FDR is controlled across the "
        "executable registered screens; no result changes deployment automatically.", "",
        "## Search verdict", "",
        f"- Executable cells tested: **{len(results):,}**",
        f"- Passed every fold before search correction: **{len(pre_fdr):,}**",
        f"- Historically qualified after FDR: **{len(qualified):,}**",
        "- Capacity promotion: **not evaluated when no screen survives the historical gate**"
        if not qualified else "- Capacity promotion: **required before shadow qualification**",
        "",
    ]
    if pre_fdr:
        lines += ["### Pre-FDR survivors", "", "| hypothesis | worst-period p | FDR q | final |", "|---|---:|---:|---|"]
        for result in pre_fdr:
            lines.append(
                f"| {result['hypothesis_id']} | {result['worst_period_p']:.6f} | "
                f"{result['fdr_q']:.6f} | {result['historically_qualified']} |"
            )
        lines.append("")
    lines += [
        "## Registry", "",
        "| hypothesis | declared status | retroactive | recomputed | FDR q |", "|---|---|---:|---|---:|",
    ]
    for spec in registry["hypotheses"]:
        r = by_id.get(spec["id"])
        recomputed = r["verdict"] if r else "documented only"
        q_value = f"{r['fdr_q']:.6f}" if r else ""
        lines.append(
            f"| {spec['id']} | {spec['status']} | {spec['retroactive']} | "
            f"{recomputed} | {q_value} |"
        )
    untested = [spec for spec in registry["hypotheses"] if spec["status"] == "untested"]
    if untested:
        lines += [
            "", "## Explicitly untested dimensions", "",
            "These are registered gaps, not negative findings:", "",
        ]
        for spec in untested:
            lines.append(
                f"- **{spec['id']}** — {spec['mechanism']} "
                f"*Status: {spec['contract']['validation']}.*"
            )
    lines += ["", "## Fold evidence", "", "| hypothesis | period | n | events | mean hold | hold SE | mean ann net | ann SE | lower bound | top-10 share | tail loss | pass |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in periods:
        lines.append(
            f"| {r['hypothesis_id']} | {r['period']} | {r['n']} | {r['n_events']} | "
            f"{r['mean_hold_return']:.4f} | {r['hold_return_se']:.4f} | "
            f"{r['mean_ann_net']:.4f} | {r['cluster_se']:.4f} | {r['lower_bound']:.4f} | "
            f"{r['top10_event_share']:.3f} | {r['tail_loss_rate']:.3f} | {r['period_pass']} |"
        )
    return "\n".join(lines) + "\n"


def run() -> None:
    registry_path = RESEARCH / "hypotheses.yaml"
    registry = load_registry(registry_path)
    points = pl.read_parquet(DECISION_POINTS)
    outcomes = pl.read_parquet(OUTCOMES)
    joined = add_periods(points.join(outcomes.select("ticker", "result_yes", "resolution_time", "resolution_time_trustworthy"), on="ticker", how="inner")).with_columns(
        pl.when(pl.col("resolution_time_trustworthy"))
        .then((pl.col("resolution_time") - pl.col("decision_time")).dt.total_seconds())
        .otherwise(pl.col("scheduled_hold_seconds")).alias("hold_seconds")
    ).filter((pl.col("hold_seconds") > 0) & (pl.col("period") != "forward"))
    results, period_rows = [], []
    for spec in expand_hypotheses(registry):
        if spec["kind"] != "cell_no_maker":
            continue
        result, rows = evaluate_hypothesis(joined, spec)
        results.append(result)
        period_rows.extend(rows)
    qvals = false_discovery_adjust([r["worst_period_p"] for r in results])
    for result, q in zip(results, qvals):
        result["fdr_q"] = q
        result["passes_all_folds_pre_fdr"] = result["historically_qualified"]
        result["historically_qualified"] = result["historically_qualified"] and q <= 0.05
        if result["historically_qualified"]:
            result["verdict"] = "HISTORICALLY QUALIFIED"
        elif result["passes_all_folds_pre_fdr"]:
            result["verdict"] = "FDR FAIL"
        elif result["economic_failure_periods"]:
            result["verdict"] = "RED"
        else:
            result["verdict"] = "INSUFFICIENT SUPPORT"
    # Parallel grouped reductions can differ by machine epsilon depending on
    # thread scheduling. Quantize persisted evidence so identical inputs produce
    # byte-identical reports and parquet artifacts.
    for row in [*results, *period_rows]:
        for key, value in row.items():
            if isinstance(value, float) and math.isfinite(value):
                row[key] = round(value, 6)
    ATLAS_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    result_frame = pl.DataFrame(results)
    period_frame = pl.DataFrame(period_rows).join(
        result_frame.select(
            "hypothesis_id", "fdr_q", "passes_all_folds_pre_fdr", "historically_qualified",
            "verdict", "insufficient_periods", "economic_failure_periods",
        ),
        on="hypothesis_id",
        how="left",
    )
    period_frame.write_parquet(ATLAS_RESULTS)
    inputs = [DECISION_POINTS, OUTCOMES, registry_path]
    input_hash = _manifest_hash(inputs)
    (RESEARCH / "edge-atlas.md").write_text(_markdown(registry, results, period_rows, input_hash))
    (ATLAS_RESULTS.parent / "atlas_manifest.json").write_text(json.dumps({
        "registry_sha256": registry["sha256"], "input_manifest_sha256": input_hash,
        "sealed_forward_start": SEALED_FORWARD_START.isoformat(), "hypotheses_run": len(results),
    }, indent=2, sort_keys=True))
    print(f"atlas: {len(results)} executable hypotheses -> {RESEARCH / 'edge-atlas.md'}")


if __name__ == "__main__":
    run()
