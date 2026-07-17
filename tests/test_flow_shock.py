import datetime as dt

import polars as pl

from kalshi_data.analysis.flow_shock import (
    attach_forward_changes,
    build_hourly_bars,
    gate_verdict,
    select_shocks,
)

UTC = dt.timezone.utc


def _markets():
    return pl.DataFrame(
        [
            {
                "ticker": "A",
                "event_ticker": "EV-A",
                "category": "Politics",
                "fee_type": "quadratic",
                "result": "no",
                "end_time": dt.datetime(2026, 5, 1, tzinfo=UTC),
            }
        ]
    )


def _trade(ts, price, count, side="yes", block=False):
    return {
        "ticker": "A",
        "trade_id": f"{ts.isoformat()}-{price}-{count}-{side}-{block}",
        "created_time": ts,
        "yes_price_cents": price,
        "count": float(count),
        "taker_side": side,
        "is_block_trade": block,
    }


def test_hourly_signal_uses_prior_median_and_keeps_first_market_shock():
    start = dt.datetime(2026, 1, 1, tzinfo=UTC)
    rows = [_trade(start + dt.timedelta(hours=i, minutes=5), 3, 10) for i in range(10)]
    # 250 YES + 50 NO contracts, 83% YES share, price rises 3c -> 5c.
    shock_hour = start + dt.timedelta(hours=10)
    rows += [
        _trade(shock_hour + dt.timedelta(minutes=5), 5, 100),
        _trade(shock_hour + dt.timedelta(minutes=20), 5, 150),
        _trade(shock_hour + dt.timedelta(minutes=30), 5, 50, side="no"),
    ]
    # A second qualifying hour must not create a second signal for the market.
    rows += [_trade(shock_hour + dt.timedelta(hours=1, minutes=5), 8, 500)]
    # Block volume must never help form a signal.
    rows += [_trade(shock_hour + dt.timedelta(hours=2, minutes=5), 10, 10_000, block=True)]

    bars = build_hourly_bars(pl.DataFrame(rows), _markets())
    shocks = select_shocks(bars)

    assert shocks.height == 1
    signal = shocks.row(0, named=True)
    assert signal["shock_price"] == 5
    assert signal["yes_volume"] == 250
    assert signal["signal_ts"] == shock_hour + dt.timedelta(hours=1)


def test_stale_previous_bar_cannot_create_shock():
    start = dt.datetime(2026, 1, 1, tzinfo=UTC)
    rows = [_trade(start + dt.timedelta(hours=i), 3, 10) for i in range(10)]
    rows.append(_trade(start + dt.timedelta(days=3), 6, 500))

    shocks = select_shocks(build_hourly_bars(pl.DataFrame(rows), _markets()))

    assert shocks.is_empty()


def test_forward_change_uses_post_signal_trade_and_zero_imputes_missing():
    signal_ts = dt.datetime(2026, 1, 2, tzinfo=UTC)
    shocks = pl.DataFrame(
        [
            {"ticker": "A", "signal_ts": signal_ts, "shock_price": 5},
            {"ticker": "B", "signal_ts": signal_ts, "shock_price": 7},
        ]
    )
    tape = pl.DataFrame(
        [
            {"ticker": "A", "trade_id": "before", "created_time": signal_ts - dt.timedelta(minutes=1), "yes_price_cents": 9},
            {"ticker": "A", "trade_id": "after", "created_time": signal_ts + dt.timedelta(hours=20), "yes_price_cents": 3},
        ]
    )

    out = attach_forward_changes(shocks, tape, horizons_hours=(24,))
    a = out.filter(pl.col("ticker") == "A").row(0, named=True)
    b = out.filter(pl.col("ticker") == "B").row(0, named=True)

    assert a["change_24h"] == -2
    assert a["has_followup_24h"] is True
    assert b["change_24h"] is None
    assert b["change_24h_zero"] == 0


def test_gate_requires_every_metric_in_both_periods():
    good = {
        period: {
            "n": 200,
            "events": 100,
            "change_168h_zero_mean": -1.0,
            "change_168h_zero_se": 0.2,
            "ann_no_carry_mean": 0.30,
            "ann_no_carry_se": 0.05,
            "uplift_mean": 0.20,
            "uplift_se": 0.05,
        }
        for period in ("discovery", "confirmation")
    }
    assert gate_verdict(good)[0] == "GREEN"

    good["confirmation"]["uplift_mean"] = 0.05
    good["confirmation"]["uplift_se"] = 0.04
    verdict, failures = gate_verdict(good)
    assert verdict == "RED"
    assert any("confirmation uplift" in failure for failure in failures)
