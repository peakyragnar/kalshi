import polars as pl

from kalshi_data.analysis.external_alpha import (
    add_strategy_economics,
    evaluate_registered_cells,
)


def test_strategy_economics_charges_spread_and_taker_fee_on_selected_side():
    frame = pl.DataFrame({
        "side": ["yes", "no"],
        "yes_price_cents": [40, 40],
        "result_yes": [1, 0],
        "hold_seconds": [86400.0, 86400.0],
    })

    out = add_strategy_economics(frame, spread_reserve_cents=2).sort("side")

    no = out.row(0, named=True)
    yes = out.row(1, named=True)
    assert no["entry_price_cents"] == 62
    assert yes["entry_price_cents"] == 42
    assert no["fee_cents"] == 2
    assert yes["fee_cents"] == 2
    assert no["hold_return"] == (100 - 62 - 2) / 62
    assert yes["hold_return"] == (100 - 42 - 2) / 42


def test_external_cells_require_hold_return_uplift_and_materialize_unsupported_search():
    rows = []
    for period in ("early", "middle", "recent"):
        for event in range(60):
            rows.append({
                "family_id": "level",
                "cell_id": "supported",
                "period": period,
                "event_ticker": f"{period}-{event}",
                "annualized_net_return": 0.20,
                "hold_return": 0.01,
                "incremental_return": 0.05,
            })
    registered = pl.DataFrame({
        "family_id": ["level", "level"],
        "cell_id": ["supported", "unsupported"],
    })

    periods, cells = evaluate_registered_cells(
        pl.DataFrame(rows), registered, minimum_events=50,
        annual_hurdle=0.07, minimum_hold_return=0.0, z=2.0,
    )

    assert periods.height == 3
    supported = cells.filter(pl.col("cell_id") == "supported").row(0, named=True)
    unsupported = cells.filter(pl.col("cell_id") == "unsupported").row(0, named=True)
    assert supported["passes_all_folds"]
    assert unsupported["search_p"] == 1.0
    assert not unsupported["historically_qualified"]
