import datetime as dt
import json

import polars as pl
import pytest

from kalshi_data.analysis.mechanism_suite import (
    add_side_economics,
    apply_search_correction,
    build_path_rows,
    build_sibling_rows,
    classify_settlement_source,
    evaluate_cells,
    load_suite_registry,
    price_bucket,
    residualize_against_baseline,
)


UTC = dt.timezone.utc


def test_suite_registry_rejects_missing_common_gate(tmp_path):
    path = tmp_path / "suite.yaml"
    path.write_text(json.dumps({"version": 1, "common_contract": {}, "families": []}))
    with pytest.raises(ValueError, match="minimum_events_per_fold"):
        load_suite_registry(path)


def test_price_bucket_boundaries_are_disjoint():
    assert [price_bucket(p) for p in (1, 5, 6, 10, 11, 20, 21, 99)] == [
        "01-05", "01-05", "06-10", "06-10", "11-20", "11-20", "21-40", "96-99"
    ]


def test_side_economics_scores_yes_and_no_without_outcome_leakage():
    frame = pl.DataFrame({
        "ticker": ["M"], "event_ticker": ["E"], "yes_price_cents": [20],
        "result_yes": [1], "fee_type": ["quadratic"], "hold_seconds": [30 * 86400],
    })
    out = add_side_economics(frame).sort("side")
    no = out.filter(pl.col("side") == "no").row(0, named=True)
    yes = out.filter(pl.col("side") == "yes").row(0, named=True)
    assert no["hold_return"] == pytest.approx(-1.0)
    assert yes["hold_return"] == pytest.approx(4.0)
    assert yes["annualized_net_return"] == pytest.approx(4 * 365 / 30 + 0.0325)


def test_path_rows_use_only_registered_earlier_and_later_decisions():
    end = dt.datetime(2026, 1, 31, tzinfo=UTC)
    points = pl.DataFrame({
        "ticker": ["M", "M", "M", "STALE", "STALE"], "event_ticker": ["E"] * 5,
        "decision_label": ["T-30d", "T-7d", "T-1d", "T-30d", "T-7d"],
        "decision_time": [
            end - dt.timedelta(days=30), end - dt.timedelta(days=7), end - dt.timedelta(days=1),
            end - dt.timedelta(days=30), end - dt.timedelta(days=7),
        ],
        "trade_time": [
            end - dt.timedelta(days=31), end - dt.timedelta(days=8), end - dt.timedelta(days=2),
            end - dt.timedelta(days=31), end - dt.timedelta(days=31),
        ],
        "yes_price_cents": [10, 20, 99, 10, 10],
    })
    out = build_path_rows(points, [("T-30d", "T-7d")])
    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["decision_time"] == end - dt.timedelta(days=7)
    assert row["prior_yes_price_cents"] == 10
    assert row["yes_price_cents"] == 20
    assert row["price_move_cents"] == 10


def test_sibling_signal_excludes_the_contracts_own_price_move():
    end = dt.datetime(2026, 1, 31, tzinfo=UTC)
    rows = []
    for ticker, event, old, new in [("A", "E", 10, 20), ("B", "E", 30, 25), ("C", "OTHER", 5, 50)]:
        rows.extend([
            {"ticker": ticker, "event_ticker": event, "decision_label": "T-7d",
             "decision_time": end - dt.timedelta(days=7), "trade_time": end - dt.timedelta(days=8),
             "yes_price_cents": old},
            {"ticker": ticker, "event_ticker": event, "decision_label": "T-1d",
             "decision_time": end - dt.timedelta(days=1), "trade_time": end - dt.timedelta(days=2),
             "yes_price_cents": new},
        ])
    out = build_sibling_rows(pl.DataFrame(rows), [("T-7d", "T-1d")]).sort("ticker")
    assert out["ticker"].to_list() == ["A", "B"]
    assert out["sibling_move_cents"].to_list() == [-5.0, 10.0]


def test_cell_gate_requires_economics_support_and_all_three_folds():
    rows = []
    for period in ("early", "middle", "recent"):
        for i in range(3):
            rows.append({
                "family_id": "f", "cell_id": "c", "period": period,
                "event_ticker": f"{period}-{i}", "annualized_net_return": 0.30,
            })
    periods, cells = evaluate_cells(
        pl.DataFrame(rows), minimum_events=3, hurdle=0.07, z=2.0
    )
    assert len(periods) == 3
    assert cells.row(0, named=True)["passes_all_folds"] is True

    weak = pl.DataFrame(rows).with_columns(
        pl.when(pl.col("period") == "middle").then(pl.lit(-0.10))
        .otherwise(pl.col("annualized_net_return")).alias("annualized_net_return")
    )
    _, failed = evaluate_cells(weak, minimum_events=3, hurdle=0.07, z=2.0)
    assert failed.row(0, named=True)["passes_all_folds"] is False


def test_conditional_gate_requires_incremental_uplift_over_matched_base():
    rows = []
    for period in ("early", "middle", "recent"):
        for i in range(4):
            rows.append({
                "family_id": "f", "cell_id": "condition", "period": period,
                "event_ticker": f"{period}-condition-{i}",
                "annualized_net_return": 0.30, "incremental_return": -0.05,
            })
    _, cells = evaluate_cells(
        pl.DataFrame(rows), minimum_events=4, hurdle=0.07, z=2.0,
        require_incremental=True,
    )
    assert cells.row(0, named=True)["passes_all_folds"] is False


def test_residualization_removes_matched_category_price_horizon_baseline():
    frame = pl.DataFrame({
        "period": ["early"] * 4, "category": ["Politics"] * 4,
        "decision_label": ["T-7d"] * 4, "price_bucket": ["01-05"] * 4,
        "side": ["no"] * 4, "condition": ["a", "a", "b", "b"],
        "annualized_net_return": [0.30, 0.30, 0.10, 0.10],
    })
    out = residualize_against_baseline(
        frame, ["period", "category", "decision_label", "price_bucket", "side"]
    )
    assert out.filter(pl.col("condition") == "a")["incremental_return"].mean() == pytest.approx(0.10)
    assert out.filter(pl.col("condition") == "b")["incremental_return"].mean() == pytest.approx(-0.10)


def test_settlement_source_classification_is_deterministic():
    assert classify_settlement_source('[{"url":"https://bls.gov/cpi"}]') == "government"
    assert classify_settlement_source('[{"url":"https://www.nasdaq.com/market"}]') == "exchange_or_data"
    assert classify_settlement_source('[{"url":"https://www.reuters.com/world"}]') == "media_or_other"
    assert classify_settlement_source("[]") == "missing"


def test_thin_zero_p_cells_cannot_make_fdr_easier_for_supported_candidate():
    cells = pl.DataFrame({
        "family_id": ["f", "f"], "cell_id": ["supported", "thin"],
        "worst_period_p": [0.01, 0.0], "minimum_fold_events": [50, 1],
        "n_periods": [3, 3], "passes_all_folds": [True, False],
    })
    out = apply_search_correction(cells, minimum_events=50)
    supported = out.filter(pl.col("cell_id") == "supported").row(0, named=True)
    thin = out.filter(pl.col("cell_id") == "thin").row(0, named=True)
    assert supported["family_fdr_q"] == pytest.approx(0.02)
    assert thin["search_p"] == 1.0
