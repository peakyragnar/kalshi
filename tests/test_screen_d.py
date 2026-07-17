import datetime as dt

import polars as pl

from kalshi_data.analysis.screen_d import trade_economics
from kalshi_data.analysis.screens import cell_stats, cluster_se

UTC = dt.timezone.utc
END = dt.datetime(2026, 3, 1, tzinfo=UTC)


def _markets(result="yes", fee_type="quadratic"):
    return pl.DataFrame(
        [
            {
                "ticker": "M1",
                "event_ticker": "EV1",
                "category": "Economics",
                "fee_type": fee_type,
                "result": result,
                "end_time": END,
            }
        ]
    )


def _trade(taker_side, p, days_before=40):
    return {
        "ticker": "M1",
        "created_time": END - dt.timedelta(days=days_before),
        "yes_price_cents": p,
        "taker_side": taker_side,
    }


def test_taker_yes_means_maker_holds_no():
    # YES taker at 30c, market settles yes: taker wins, maker (NO at 70c) loses all
    df = trade_economics(pl.DataFrame([_trade("yes", 30)]), _markets("yes"))
    row = df.row(0, named=True)
    # taker: (100 - 30 - fee 2) / 30
    assert abs(row["ret_taker"] - (100 - 30 - 2) / 30) < 1e-9
    # maker: (0 - 70 - 0) / 70 = -1.0
    assert abs(row["ret_maker"] - (-1.0)) < 1e-9


def test_taker_no_means_maker_holds_yes():
    # NO taker at 70c (yes price 30), settles no: taker wins, maker (YES) loses
    df = trade_economics(pl.DataFrame([_trade("no", 30)]), _markets("no"))
    row = df.row(0, named=True)
    assert abs(row["ret_taker"] - (100 - 70 - 2) / 70) < 1e-9
    assert abs(row["ret_maker"] - (-1.0)) < 1e-9


def test_maker_fee_only_on_designated_series():
    df0 = trade_economics(pl.DataFrame([_trade("yes", 50)]), _markets("no", "quadratic"))
    dfm = trade_economics(
        pl.DataFrame([_trade("yes", 50)]), _markets("no", "quadratic_with_maker_fees")
    )
    # maker holds NO at 50, settles no -> payoff 100; fee 0 vs 1 cent (25% of 2c, ceil'd)
    assert abs(df0.row(0, named=True)["ret_maker"] - (100 - 50 - 0) / 50) < 1e-9
    assert abs(dfm.row(0, named=True)["ret_maker"] - (100 - 50 - 1) / 50) < 1e-9


def test_horizon_and_price_buckets():
    df = trade_economics(pl.DataFrame([_trade("yes", 15, days_before=45)]), _markets())
    row = df.row(0, named=True)
    assert row["hbucket"] == "c 30-90d"
    assert row["bucket"] == "10-20"


def test_cell_stats_matches_scalar_cluster_se():
    df = pl.DataFrame(
        {
            "cell": ["a"] * 4,
            "event_ticker": ["e1", "e1", "e2", "e3"],
            "x": [1.0, 2.0, 5.0, 8.0],
        }
    )
    out = cell_stats(df, ["cell"], "x").row(0, named=True)
    assert out["n"] == 4
    assert abs(out["x_mean"] - 4.0) < 1e-12
    assert abs(out["x_se"] - cluster_se(df["x"], df["event_ticker"])) < 1e-12
