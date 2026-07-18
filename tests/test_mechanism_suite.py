import datetime as dt
import json

import polars as pl
import pytest

from kalshi_data.analysis.mechanism_suite import (
    add_side_economics,
    build_path_rows,
    classify_settlement_source,
    evaluate_cells,
    load_suite_registry,
    price_bucket,
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
        "ticker": ["M", "M", "M"], "event_ticker": ["E"] * 3,
        "decision_label": ["T-30d", "T-7d", "T-1d"],
        "decision_time": [end - dt.timedelta(days=30), end - dt.timedelta(days=7), end - dt.timedelta(days=1)],
        "yes_price_cents": [10, 20, 99],
    })
    out = build_path_rows(points, [("T-30d", "T-7d")])
    row = out.row(0, named=True)
    assert row["decision_time"] == end - dt.timedelta(days=7)
    assert row["prior_yes_price_cents"] == 10
    assert row["yes_price_cents"] == 20
    assert row["price_move_cents"] == 10


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


def test_settlement_source_classification_is_deterministic():
    assert classify_settlement_source('[{"url":"https://bls.gov/cpi"}]') == "government"
    assert classify_settlement_source('[{"url":"https://www.nasdaq.com/market"}]') == "exchange_or_data"
    assert classify_settlement_source('[{"url":"https://www.reuters.com/world"}]') == "media_or_other"
    assert classify_settlement_source("[]") == "missing"
