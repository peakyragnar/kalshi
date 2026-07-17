import datetime as dt

import polars as pl

from kalshi_data.analysis.corpus_audit import audit_corpus


UTC = dt.timezone.utc


def test_audit_exposes_missing_settlement_and_short_tape_coverage():
    now = dt.datetime(2026, 7, 17, tzinfo=UTC)
    markets = pl.DataFrame(
        {
            "ticker": ["SHORT", "EARLY"],
            "event_ticker": ["E1", "E2"],
            "series_ticker": ["S1", "S2"],
            "category": ["Politics", "Politics"],
            "tier": ["deployment", "deployment"],
            "open_time": [now - dt.timedelta(days=2), now - dt.timedelta(days=20)],
            "close_time": [now, now - dt.timedelta(days=1)],
            "expiration_time": [now, now + dt.timedelta(days=30)],
            "settled_time": [now, None],
            "can_close_early": [False, True],
            "result": ["no", "yes"],
            "volume": [10.0, 20.0],
        }
    )
    trades = pl.DataFrame({"ticker": ["SHORT"], "trade_id": ["T1"]})
    summary, coverage = audit_corpus(markets, trades, now=now)
    assert summary["markets"] == 2
    assert summary["markets_missing_settled_time"] == 1
    assert summary["traded_sub_6d_markets"] == 1
    assert summary["traded_sub_6d_markets_with_tape"] == 1
    assert len(coverage) == 2
