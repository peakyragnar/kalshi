import datetime as dt

import polars as pl
import pytest

from kalshi_data.analysis.metadata_suite import (
    build_ladder_pairs,
    build_event_coherence,
    classify_rule,
    infer_ladder_direction,
    ladder_strike,
)


UTC = dt.timezone.utc


@pytest.mark.parametrize(
    ("subtitle", "rules", "expected"),
    [
        ("$50,000 or above", "", "above"),
        ("$50,000 or above", "Values below the threshold settle No", "above"),
        ("Below 3.0%", "", "below"),
        ("Between 2% and 4%", "", None),
        (None, "The value is greater than 10", "above"),
    ],
)
def test_ladder_direction_requires_unambiguous_ordering(subtitle, rules, expected):
    assert infer_ladder_direction(subtitle, rules) == expected


def test_ladder_strike_uses_cap_for_below_contracts():
    assert ladder_strike("below", floor_strike=10.0, cap_strike=20.0) == 20.0
    assert ladder_strike("above", floor_strike=10.0, cap_strike=20.0) == 10.0
    assert ladder_strike("below", floor_strike=10.0, cap_strike=None) == 10.0


def test_rule_classifier_prioritizes_judgment_language_over_numeric_strike():
    assert classify_rule(
        "The agency must substantially acknowledge responsibility", floor_strike=10
    ) == "judgment_or_attribution"
    assert classify_rule("Resolves Yes if the reported value is 10 or above", floor_strike=10) == "numeric_objective"
    assert classify_rule("Resolves Yes when the bill is signed into law") == "official_act"
    assert classify_rule(None) == "unclassified"
    assert classify_rule(None, expiration_value="") == "unclassified"
    assert classify_rule(None, expiration_value="Yes") == "unclassified"


def test_ladder_pairs_compute_correct_signed_monotonic_gap_and_pair_cost():
    now = dt.datetime(2026, 1, 1, tzinfo=UTC)
    frame = pl.DataFrame({
        "ticker": ["A", "B", "C", "D"],
        "event_ticker": ["E1", "E1", "E2", "E2"],
        "decision_label": ["T-7d"] * 4,
        "decision_time": [now] * 4,
        "trade_time": [now - dt.timedelta(minutes=1)] * 4,
        "scheduled_hold_seconds": [7 * 86400] * 4,
        "direction": ["above", "above", "below", "below"],
        "floor_strike": [10.0, 20.0, 10.0, 20.0],
        "yes_price_cents": [30, 40, 40, 30],
    })
    out = build_ladder_pairs(frame).sort("event_ticker")
    assert len(out) == 2
    above, below = out.iter_rows(named=True)
    assert above["signed_gap_cents"] == 10
    assert below["signed_gap_cents"] == 10
    assert above["pair_cost_cents"] == 90
    assert above["paired_return_proxy"] == pytest.approx(10 / 90)


def test_ladder_pairs_only_compare_adjacent_strikes_within_same_event_and_label():
    now = dt.datetime(2026, 1, 1, tzinfo=UTC)
    frame = pl.DataFrame({
        "ticker": ["A", "B", "C"], "event_ticker": ["E"] * 3,
        "decision_label": ["T-7d"] * 3, "decision_time": [now] * 3,
        "trade_time": [now] * 3, "scheduled_hold_seconds": [86400] * 3,
        "direction": ["above"] * 3, "floor_strike": [1.0, 2.0, 3.0],
        "yes_price_cents": [20, 19, 18],
    })
    out = build_ladder_pairs(frame)
    assert len(out) == 2
    assert set(out["higher_ticker"].to_list()) == {"B", "C"}


def test_event_coherence_sums_all_choices_and_records_time_skew():
    now = dt.datetime(2026, 1, 1, tzinfo=UTC)
    frame = pl.DataFrame({
        "ticker": ["A", "B", "C"], "event_ticker": ["E"] * 3,
        "decision_label": ["T-7d"] * 3, "decision_time": [now] * 3,
        "trade_time": [now, now - dt.timedelta(minutes=2), now - dt.timedelta(minutes=7)],
        "yes_price_cents": [40, 35, 30], "is_exclusive_group": [True] * 3,
        "expected_contracts": [3] * 3,
    })
    row = build_event_coherence(frame).row(0, named=True)
    assert row["contracts"] == 3
    assert row["yes_price_sum_cents"] == 105
    assert row["dislocation_cents"] == 5
    assert row["dislocation_side"] == "buy_all_no"
    assert row["trade_time_skew_seconds"] == 420


def test_event_coherence_rejects_incomplete_multi_leg_price_sets():
    now = dt.datetime(2026, 1, 1, tzinfo=UTC)
    frame = pl.DataFrame({
        "ticker": ["A", "B"], "event_ticker": ["E", "E"],
        "decision_label": ["T-7d", "T-7d"], "decision_time": [now, now],
        "trade_time": [now, now], "yes_price_cents": [30, 30],
        "is_exclusive_group": [True, True], "expected_contracts": [3, 3],
    })
    assert build_event_coherence(frame).is_empty()
