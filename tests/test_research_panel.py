import datetime as dt

import polars as pl

from kalshi_data.analysis.research_panel import (
    DecisionSpec,
    build_decision_points,
    build_market_relations,
    build_outcomes,
    enrich_outcomes_with_metadata,
    exclude_red_rulebooks,
)


UTC = dt.timezone.utc


def test_research_universe_excludes_red_rulebooks_but_keeps_unswept_and_yellow():
    markets = pl.DataFrame({
        "series_ticker": ["GOOD", "YELLOW", "BAD"],
        "ticker": ["GOOD-1", "YELLOW-1", "BAD-1"],
    })
    verdicts = {
        "YELLOW": {"verdict": "YELLOW"},
        "BAD": {"verdict": "RED"},
    }
    out = exclude_red_rulebooks(markets, verdicts)
    assert out["ticker"].to_list() == ["GOOD-1", "YELLOW-1"]


def _market(**overrides):
    end = dt.datetime(2026, 1, 10, tzinfo=UTC)
    row = {
        "ticker": "M1",
        "event_ticker": "EV1",
        "series_ticker": "S1",
        "category": "Politics",
        "tier": "deployment",
        "frequency": "one_off",
        "fee_type": "quadratic",
        "fee_multiplier": 1,
        "market_type": "binary",
        "can_close_early": False,
        "open_time": end - dt.timedelta(days=10),
        "close_time": end,
        "expiration_time": end,
        "settled_time": end,
        "result": "no",
        "volume": 100.0,
    }
    return {**row, **overrides}


def _trade(ts, price, side="yes", count=1.0, ticker="M1"):
    return {
        "ticker": ticker,
        "trade_id": f"{ticker}-{ts.isoformat()}-{price}",
        "created_time": ts,
        "yes_price_cents": price,
        "count": count,
        "taker_side": side,
        "is_block_trade": False,
    }


def test_decision_point_uses_only_information_available_at_decision():
    end = dt.datetime(2026, 1, 10, tzinfo=UTC)
    markets = pl.DataFrame([_market()])
    trades = pl.DataFrame(
        [
            _trade(end - dt.timedelta(days=2), 10, "yes", 3),
            _trade(end - dt.timedelta(hours=12), 80, "no", 7),
        ]
    )
    out = build_decision_points(
        markets,
        trades,
        [DecisionSpec("close", "T-1d", dt.timedelta(days=1))],
    )
    row = out.row(0, named=True)
    assert row["yes_price_cents"] == 10
    assert row["trade_time"] == end - dt.timedelta(days=2)
    assert row["cumulative_volume"] == 3.0
    assert row["decision_time"] == end - dt.timedelta(days=1)


def test_short_duration_close_anchors_and_listing_anchors_are_supported():
    end = dt.datetime(2026, 1, 10, tzinfo=UTC)
    market = _market(open_time=end - dt.timedelta(days=2))
    markets = pl.DataFrame([market])
    trades = pl.DataFrame([_trade(end - dt.timedelta(hours=30), 20)])
    specs = [
        DecisionSpec("close", "T-6h", dt.timedelta(hours=6)),
        DecisionSpec("listing", "L+1d", dt.timedelta(days=1)),
        DecisionSpec("close", "T-3d", dt.timedelta(days=3)),
    ]
    out = build_decision_points(markets, trades, specs)
    assert set(out["decision_label"]) == {"T-6h", "L+1d"}


def test_finalized_close_time_is_the_trustworthy_trading_boundary():
    end = dt.datetime(2026, 1, 10, tzinfo=UTC)
    markets = pl.DataFrame([_market(can_close_early=True, settled_time=None)])
    trades = pl.DataFrame([_trade(end - dt.timedelta(days=2), 10)])
    out = build_decision_points(
        markets,
        trades,
        [DecisionSpec("close", "T-1d", dt.timedelta(days=1))],
    )
    assert out.row(0, named=True)["decision_time_trustworthy"] is True


def test_outcomes_are_separate_and_preserve_resolution_quality():
    end = dt.datetime(2026, 1, 10, tzinfo=UTC)
    out = build_outcomes(pl.DataFrame([_market(settled_time=None, can_close_early=True)]))
    row = out.row(0, named=True)
    assert row["result_yes"] == 0
    assert row["resolution_time"] is None
    assert row["resolution_time_trustworthy"] is False
    assert "yes_price_cents" not in out.columns


def test_metadata_settlement_timestamp_repairs_missing_resolution_time():
    outcomes = build_outcomes(pl.DataFrame([_market(settled_time=None, can_close_early=True)]))
    metadata = pl.DataFrame({"ticker": ["M1"], "settled_time": ["2026-01-15T12:00:00Z"]})
    row = enrich_outcomes_with_metadata(outcomes, metadata).row(0, named=True)
    assert row["resolution_time"] == dt.datetime(2026, 1, 15, 12, tzinfo=UTC)
    assert row["resolution_time_trustworthy"] is True


def test_relations_are_memberships_not_quadratic_pairs():
    markets = pl.DataFrame(
        [
            _market(ticker="M1", volume=10.0),
            _market(ticker="M2", volume=20.0),
            _market(ticker="M3", event_ticker="EV2", volume=5.0),
        ]
    )
    out = build_market_relations(markets)
    assert len(out) == 3
    ev1 = out.filter(pl.col("event_ticker") == "EV1")
    assert set(ev1["event_group_size"]) == {2}
    assert set(ev1["event_group_volume"]) == {30.0}


def test_two_labels_at_same_timestamp_do_not_cartesian_duplicate():
    end = dt.datetime(2026, 1, 10, tzinfo=UTC)
    markets = pl.DataFrame([_market(open_time=end - dt.timedelta(days=2))])
    trades = pl.DataFrame([_trade(end - dt.timedelta(days=2), 10)])
    out = build_decision_points(
        markets,
        trades,
        [
            DecisionSpec("close", "T-1d", dt.timedelta(days=1)),
            DecisionSpec("listing", "L+1d", dt.timedelta(days=1)),
        ],
    )
    assert len(out) == 2
    assert set(out["decision_label"]) == {"T-1d", "L+1d"}
