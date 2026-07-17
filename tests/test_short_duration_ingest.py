import datetime as dt

import polars as pl

from kalshi_data.ingest.trades import eligible_markets_from_frame, fetch_market_trades


UTC = dt.timezone.utc


def test_default_eligibility_includes_sub_six_day_deployment_market():
    end = dt.datetime(2026, 7, 17, tzinfo=UTC)
    markets = pl.DataFrame(
        {
            "ticker": ["SHORT", "ZERO", "SPORT"],
            "tier": ["deployment", "deployment", "instrumentation"],
            "volume": [10.0, 0.0, 50.0],
            "open_time": [end - dt.timedelta(hours=12)] * 3,
            "close_time": [end] * 3,
            "expiration_time": [end] * 3,
        }
    )
    out = eligible_markets_from_frame(markets, "deployment")
    assert out["ticker"].to_list() == ["SHORT"]


def test_trade_fetch_routes_across_dynamic_cutoff_and_deduplicates():
    cutoff = dt.datetime(2026, 5, 1, tzinfo=UTC)

    class Client:
        def paginate(self, path, key, **params):
            assert params["ticker"] == "M1"
            common = {"ticker": "M1", "trade_id": "same", "created_time": "2026-05-01T00:00:00Z", "yes_price": 10, "count": 1}
            return iter([[common]])

    rows = fetch_market_trades(
        Client(),
        "M1",
        cutoff - dt.timedelta(days=1),
        cutoff + dt.timedelta(days=1),
        trade_cutoff=cutoff,
    )
    assert len(rows) == 1


def test_lifetime_filter_uses_trading_close_not_rescheduling_ceiling():
    end = dt.datetime(2026, 7, 17, tzinfo=UTC)
    markets = pl.DataFrame({
        "ticker": ["SHORT"], "tier": ["deployment"], "volume": [10.0],
        "open_time": [end - dt.timedelta(hours=12)], "close_time": [end],
        "expiration_time": [end + dt.timedelta(days=7)],
    })
    assert len(eligible_markets_from_frame(markets, "deployment", min_lifetime_days=6)) == 0
