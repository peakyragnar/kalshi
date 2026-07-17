import datetime as dt

import polars as pl

from kalshi_data.analysis.base_rates import add_labels, family_stats, neighborhood_population

STATS_COLS = [
    "category", "series_ticker", "n", "n_events", "n_markets",
    "implied", "tail_rate", "tail_se", "ann_mean", "ann_se", "firing_events",
]


def _row(**kw):
    base = {
        "category": "Politics", "series_ticker": "KXTEST", "n": 60, "n_events": 30,
        "n_markets": 60, "implied": 0.03, "tail_rate": 0.0, "tail_se": 0.0,
        "ann_mean": 0.30, "ann_se": 0.05, "firing_events": 0,
    }
    base.update(kw)
    return pl.DataFrame([base])


def test_trap_when_tail_rate_meets_price_with_two_firing_events():
    out = add_labels(_row(tail_rate=0.16, tail_se=0.05, implied=0.10, firing_events=6))
    assert out["label"][0] == "TRAP"


def test_single_firing_event_is_not_a_trap():
    out = add_labels(_row(tail_rate=0.16, tail_se=0.05, implied=0.10, firing_events=1))
    assert out["label"][0] != "TRAP"


def test_fat_needs_upper_band_below_price_and_map_bar():
    out = add_labels(_row(n=80, n_events=120, implied=0.05, ann_mean=0.30, ann_se=0.08))
    # zero fires, 120 events: q_hi = 3/120 = 0.025 < 0.05, and 0.30 - 2*0.08 > 0.07
    assert out["q_hi"][0] == 0.025
    assert out["label"][0] == "FAT"


def test_fat_denied_when_ann_bar_fails():
    out = add_labels(_row(n=80, n_events=120, implied=0.05, ann_mean=0.15, ann_se=0.05))
    assert out["label"][0] != "FAT"  # 0.15 - 2*0.05 = 0.05 < hurdle


def test_thin_when_too_few_events():
    out = add_labels(_row(n_events=5))
    assert out["label"][0] == "THIN"


def test_thin_when_zero_fires_cannot_distinguish_double_overpricing():
    # 20 events, priced 3c: q_hi = 3/20 = 0.15 > 2 * 0.03 -> underpowered
    out = add_labels(_row(n_events=20, implied=0.03))
    assert out["label"][0] == "THIN"


def test_rule_of_three_upper_band_only_when_no_fires():
    zero = add_labels(_row(n_events=30))
    assert zero["q_hi"][0] == 0.10
    fired = add_labels(_row(tail_rate=0.10, tail_se=0.02, firing_events=3, implied=0.20))
    assert abs(fired["q_hi"][0] - (0.10 + 1.96 * 0.02)) < 1e-9


def test_no_fat_without_return_columns():
    # tier 2 carries no return stats; a FAT-looking family must stay NEUTRAL
    out = add_labels(
        _row(n=80, n_events=120, implied=0.05, ann_mean=None, ann_se=None)
    )
    assert out["q_hi"][0] == 0.025
    assert out["label"][0] == "NEUTRAL"


def test_neighborhood_dedupes_by_anchor_preference():
    ts = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    df = pl.DataFrame(
        {
            "category": ["Politics"] * 3,
            "ticker": ["KXA-1", "KXA-1", "KXA-2"],
            "event_ticker": ["E1"] * 3,
            "horizon_days": [7, 30, 30],
            "yes_price_cents": [3, 5, 40],
            "snap_ts": [ts] * 3,
            "hold_days": [7, 30, 30],
            "result_yes": [0, 0, 1],
        }
    )
    out = neighborhood_population(df)
    # KXA-1 keeps only its 30d row (the cell's own anchor); KXA-2 is not a longshot
    assert out["ticker"].to_list() == ["KXA-1"]
    assert out["yes_price_cents"][0] == 5
    assert out["period"][0] == "confirmation"


def test_family_stats_counts_and_clusters():
    df = pl.DataFrame(
        {
            "category": ["Politics"] * 4,
            "series_ticker": ["KXA"] * 4,
            "ticker": ["KXA-1", "KXA-2", "KXA-3", "KXA-4"],
            "event_ticker": ["E1", "E1", "E2", "E3"],
            "yes_price_cents": [2, 4, 2, 4],
            "result_yes": [0, 0, 1, 0],
            "ann_no_carry": [0.5, 0.5, -12.0, 0.5],
        }
    )
    out = family_stats(df)
    assert out["n"][0] == 4
    assert out["n_events"][0] == 3
    assert out["n_markets"][0] == 4
    assert out["implied"][0] == 0.03
    assert out["tail_rate"][0] == 0.25
    assert out["firing_events"][0] == 1
