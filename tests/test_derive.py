import datetime as dt

import polars as pl

from kalshi_data.analysis.derive import build_snapshots

UTC = dt.timezone.utc


def _markets(rows):
    base = {
        "series_ticker": "KXTEST",
        "event_ticker": "KXTEST-EV",
        "category": "Economics",
        "tier": "deployment",
        "fee_type": "quadratic",
        "fee_multiplier": 1,
        "settled_time": None,
        "volume": 100.0,
    }
    return pl.DataFrame([{**base, **r} for r in rows]).with_columns(
        pl.col("settled_time").cast(pl.Datetime(time_zone="UTC"))
    )


def _trades(rows):
    return pl.DataFrame(rows)


def test_snapshot_takes_last_trade_before_horizon_with_staleness():
    exp = dt.datetime(2026, 3, 1, tzinfo=UTC)
    markets = _markets(
        [
            {
                "ticker": "M1",
                "open_time": exp - dt.timedelta(days=60),
                "close_time": exp,
                "expiration_time": exp,
                "result": "yes",
            }
        ]
    )
    trades = _trades(
        [
            # 10 days before expiration: last trade before the T-7d snapshot
            {"ticker": "M1", "created_time": exp - dt.timedelta(days=10), "yes_price_cents": 80, "count": 5.0},
            # 2 days before expiration: after the T-7d snapshot, must be ignored
            {"ticker": "M1", "created_time": exp - dt.timedelta(days=2), "yes_price_cents": 95, "count": 5.0},
        ]
    )
    out = build_snapshots(markets, trades)
    t7 = out.filter(pl.col("horizon_days") == 7).row(0, named=True)
    assert t7["yes_price_cents"] == 80
    assert t7["staleness_s"] == 3 * 86400
    assert t7["cum_volume"] == 5.0
    assert t7["result_yes"] == 1
    assert t7["hold_days"] == 7


def test_horizons_beyond_market_lifetime_are_absent():
    exp = dt.datetime(2026, 3, 1, tzinfo=UTC)
    markets = _markets(
        [
            {
                "ticker": "M2",
                "open_time": exp - dt.timedelta(days=40),
                "close_time": exp,
                "expiration_time": exp,
                "result": "no",
            }
        ]
    )
    trades = _trades(
        [{"ticker": "M2", "created_time": exp - dt.timedelta(days=39), "yes_price_cents": 30, "count": 1.0}]
    )
    out = build_snapshots(markets, trades)
    horizons = sorted(out["horizon_days"].to_list())
    assert horizons == [7, 30]  # 90/180/365 predate the market's open


def test_no_trades_before_snapshot_means_no_row():
    exp = dt.datetime(2026, 3, 1, tzinfo=UTC)
    markets = _markets(
        [
            {
                "ticker": "M3",
                "open_time": exp - dt.timedelta(days=60),
                "close_time": exp,
                "expiration_time": exp,
                "result": "yes",
            }
        ]
    )
    trades = _trades(
        [{"ticker": "M3", "created_time": exp - dt.timedelta(days=10), "yes_price_cents": 99, "count": 1.0}]
    )
    out = build_snapshots(markets, trades)
    assert len(out.filter(pl.col("horizon_days") == 7)) == 1  # trade at T-10d serves T-7d
    assert len(out.filter(pl.col("horizon_days") == 30)) == 0  # but predates nothing at T-30d


def test_cumulative_volume_is_as_of_snapshot_not_total():
    exp = dt.datetime(2026, 3, 1, tzinfo=UTC)
    markets = _markets(
        [
            {
                "ticker": "M4",
                "open_time": exp - dt.timedelta(days=60),
                "close_time": exp,
                "expiration_time": exp,
                "result": "yes",
            }
        ]
    )
    trades = _trades(
        [
            {"ticker": "M4", "created_time": exp - dt.timedelta(days=45), "yes_price_cents": 50, "count": 10.0},
            {"ticker": "M4", "created_time": exp - dt.timedelta(days=35), "yes_price_cents": 55, "count": 20.0},
            {"ticker": "M4", "created_time": exp - dt.timedelta(days=1), "yes_price_cents": 90, "count": 100.0},
        ]
    )
    out = build_snapshots(markets, trades)
    t30 = out.filter(pl.col("horizon_days") == 30).row(0, named=True)
    assert t30["yes_price_cents"] == 55
    assert t30["cum_volume"] == 30.0
