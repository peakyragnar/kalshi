import datetime as dt
import json

import polars as pl

from kalshi_data.core.parse import market_row
from kalshi_data.ingest import incremental
from kalshi_data.ingest.incremental import select_new_rows

SERIES = {
    "KXCPI": {"ticker": "KXCPI", "category": "Economics", "tier": "deployment",
              "frequency": "monthly", "fee_type": "quadratic", "fee_multiplier": 1, "title": "CPI"},
    "KXNFLGAME": {"ticker": "KXNFLGAME", "category": "Sports", "tier": "instrumentation",
                  "frequency": "daily", "fee_type": "quadratic", "fee_multiplier": 1, "title": "NFL"},
}


def _m(ticker, series):
    return {"ticker": ticker, "series_ticker": series, "event_ticker": f"{series}-EV",
            "status": "settled", "result": "no", "close_time": "2026-07-17T00:00:00Z"}


def test_keeps_only_new_deployment_rows():
    page = [
        _m("KXCPI-26JUL-T3", "KXCPI"),            # new deployment -> keep
        _m("KXCPI-26JUN-T3", "KXCPI"),            # already stored -> skip
        _m("KXNFLGAME-X", "KXNFLGAME"),           # instrumentation -> skip
        _m("KXMVESPORTS-S1-A", "KXMVESPORTS"),    # parlay, unknown series -> excluded tier
    ]
    out = select_new_rows(page, SERIES, existing={"KXCPI-26JUN-T3"})
    assert [r["ticker"] for r in out] == ["KXCPI-26JUL-T3"]
    assert out[0]["tier"] == "deployment"
    assert out[0]["category"] == "Economics"


def test_unknown_new_series_classified_fresh():
    # a series created after the catalog snapshot, sports-prefixed -> not deployment
    page = [_m("KXMVENEW-S9-Z", "KXMVENEW")]
    assert select_new_rows(page, {}, set()) == []


def test_same_day_rerun_merges_incremental_partitions(tmp_path, monkeypatch):
    markets_dir = tmp_path / "markets"
    trades_dir = tmp_path / "trades"
    checkpoints = tmp_path / "checkpoints"
    markets_dir.mkdir()
    trades_dir.mkdir()
    checkpoints.mkdir()

    meta = SERIES["KXCPI"]

    def market(ticker):
        return {
            "ticker": ticker,
            "series_ticker": "KXCPI",
            "event_ticker": "KXCPI-26JUL",
            "market_type": "binary",
            "status": "settled",
            "result": "no",
            "open_time": "2026-07-01T00:00:00Z",
            "close_time": "2026-07-17T06:00:00Z",
            "expiration_time": "2026-07-17T06:00:00Z",
            "settled_time": "2026-07-17T06:00:00Z",
            "last_price": 4,
            "volume": 30,
        }

    market_path = markets_dir / "incr-20260717.parquet"
    pl.DataFrame([market_row(market("KXCPI-OLD"), meta)]).write_parquet(market_path)
    trade_path = trades_dir / "incr-20260717.parquet"
    pl.DataFrame(
        [
            {
                "ticker": "KXCPI-OLD",
                "trade_id": "old-trade",
                "created_time": "2026-07-10T00:00:00Z",
                "yes_price_cents": 4,
                "count": 1.0,
                "taker_side": "yes",
                "is_block_trade": False,
            }
        ]
    ).write_parquet(trade_path)
    checkpoint = checkpoints / "incremental.json"
    checkpoint.write_text(json.dumps({"high_water": "2026-07-17T07:00:00+00:00"}))

    class FrozenDateTime(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 7, 17, 12, 0, tzinfo=tz)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def paginate(self, path, list_key, **kwargs):
            assert path == "/markets"
            return iter([[market("KXCPI-NEW")]])

    def fake_trades(client, ticker, open_time, end_time):
        return [
            {
                "ticker": ticker,
                "trade_id": "new-trade",
                "created_time": "2026-07-17T05:00:00Z",
                "yes_price_cents": 5,
                "count": 2.0,
                "taker_side": "yes",
                "is_block_trade": False,
            }
        ]

    monkeypatch.setattr(incremental, "MARKETS", markets_dir)
    monkeypatch.setattr(incremental, "TRADES", trades_dir)
    monkeypatch.setattr(incremental, "CHECKPOINT", checkpoint)
    monkeypatch.setattr(incremental.dt, "datetime", FrozenDateTime)
    monkeypatch.setattr(incremental, "KalshiClient", FakeClient)
    monkeypatch.setattr(incremental.ingest_series, "run", lambda client: pl.DataFrame([meta]))
    monkeypatch.setattr(incremental, "fetch_market_trades", fake_trades)
    monkeypatch.setattr(incremental.derive, "run", lambda: None)

    incremental.run()

    assert set(pl.read_parquet(market_path)["ticker"]) == {"KXCPI-OLD", "KXCPI-NEW"}
    assert set(pl.read_parquet(trade_path)["trade_id"]) == {"old-trade", "new-trade"}
