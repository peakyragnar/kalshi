import datetime as dt
import threading

import httpx
import polars as pl

from kalshi_data.ingest import trades
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


def test_parallel_run_commits_trade_rows_and_market_checkpoint(monkeypatch, tmp_path):
    now = dt.datetime(2026, 7, 18, tzinfo=UTC)
    eligible = pl.DataFrame(
        {
            "ticker": ["M1", "M2"],
            "open_time": [now - dt.timedelta(days=1)] * 2,
            "end_time": [now] * 2,
        }
    )
    monkeypatch.setattr(trades, "eligible_markets", lambda *_: eligible)
    monkeypatch.setattr(trades, "trade_cutoff", lambda _: now)
    monkeypatch.setattr(trades, "CHECKPOINT", tmp_path / "checkpoint.json")
    monkeypatch.setattr(trades, "TRADES_DIR", tmp_path / "shards")

    def fake_worker(task):
        market, _, _ = task
        ticker = market["ticker"]
        return ticker, [{
            "ticker": ticker,
            "trade_id": f"trade-{ticker}",
            "created_time": now.isoformat(),
            "yes_price_cents": 50.0,
            "count": 1.0,
            "taker_side": "yes",
            "is_block_trade": False,
        }], None

    monkeypatch.setattr(trades, "_fetch_worker", fake_worker)
    trades.run("deployment", workers=2)

    assert set(trades._load_checkpoint()["done"]) == {"M1", "M2"}
    assert pl.read_parquet(tmp_path / "shards" / "*.parquet").sort("ticker")["ticker"].to_list() == [
        "M1",
        "M2",
    ]


def test_worker_records_historical_404_as_unavailable(monkeypatch):
    now = dt.datetime(2026, 7, 18, tzinfo=UTC)
    monkeypatch.setattr(trades, "_thread_state", threading.local())

    def unavailable(*args, **kwargs):
        request = httpx.Request("GET", "https://example.test/historical/trades")
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError("missing", request=request, response=response)

    monkeypatch.setattr(trades, "fetch_market_trades", unavailable)
    ticker, rows, error = trades._fetch_worker((
        {"ticker": "MISSING", "open_time": now, "end_time": now}, now, 1.0
    ))

    assert ticker == "MISSING"
    assert rows == []
    assert "404" in error
