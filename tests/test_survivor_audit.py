import datetime as dt

import polars as pl
import pytest

from kalshi_data.analysis.survivor_audit import (
    add_fill_execution_economics,
    match_candidate_prints,
)


UTC = dt.timezone.utc


def test_candidate_execution_distinguishes_maker_no_from_taker_no():
    frame = pl.DataFrame({
        "ticker": ["M", "M"], "event_ticker": ["E", "E"],
        "period": ["early", "early"], "category": ["Economics", "Economics"],
        "series_ticker": ["S", "S"], "yes_price_cents": [3, 3],
        "result_yes": [0, 0], "fee_type": ["quadratic", "quadratic"],
        "hold_seconds": [86400, 86400], "taker_side": ["yes", "no"],
        "count": [10.0, 5.0],
    })
    out = add_fill_execution_economics(frame).sort("execution_role")
    maker = out.filter(pl.col("execution_role") == "maker_no").row(0, named=True)
    taker = out.filter(pl.col("execution_role") == "taker_no").row(0, named=True)
    assert maker["hold_return"] == pytest.approx(3 / 97)
    assert taker["hold_return"] == pytest.approx(2 / 97)
    assert maker["contracts"] == 10.0
    assert taker["contracts"] == 5.0


def test_candidate_print_match_requires_exact_price_at_shared_timestamp():
    now = dt.datetime(2026, 1, 1, tzinfo=UTC)
    path = pl.DataFrame({
        "ticker": ["M"], "trade_time": [now], "yes_price_cents": [3],
    })
    tape = pl.DataFrame({
        "ticker": ["M", "M"], "trade_time": [now, now],
        "yes_price_cents": [3, 4], "count": [10, 100],
    })
    out = match_candidate_prints(path, tape)
    assert len(out) == 1
    assert out.row(0, named=True)["count"] == 10
