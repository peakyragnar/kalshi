import polars as pl

from kalshi_data.analysis.weather_alpha_v2 import (
    BIN_EDGES,
    apply_recalibration,
    fit_recalibration,
    maker_economics,
)


def test_fit_recalibration_maps_bins_to_realized_rates_monotonically():
    # bin (0.1, 0.2]: 100 samples, 2 fired -> ~2.4% with Jeffreys smoothing
    raw = [0.15] * 100 + [0.001] * 200
    out = [1] * 2 + [0] * 98 + [0] * 200
    table = fit_recalibration(raw, out)
    assert len(table) == len(BIN_EDGES) - 1
    hot = apply_recalibration(table, 0.15)
    cold = apply_recalibration(table, 0.001)
    assert 0.015 < hot < 0.035
    assert cold < 0.01
    # monotone: higher raw probability never maps lower
    assert hot >= cold
    values = [apply_recalibration(table, e + 1e-9) for e in BIN_EDGES[:-1]]
    assert values == sorted(values)


def test_fit_recalibration_empty_bins_inherit_previous_value():
    raw = [0.001] * 100
    out = [0] * 100
    table = fit_recalibration(raw, out)
    # bins above the only populated one carry its value forward, never None
    assert apply_recalibration(table, 0.9) == apply_recalibration(table, 0.001)


def test_apply_recalibration_none_passthrough():
    assert apply_recalibration([0.1] * (len(BIN_EDGES) - 1), None) is None


def test_maker_economics_no_side_no_reserve_no_taker_fee():
    frame = pl.DataFrame({
        "side": ["no", "no"],
        "yes_price_cents": [3, 3],
        "fee_type": ["quadratic", "quadratic"],
        "result_yes": [0, 1],
        "hold_seconds": [86400, 86400],
    })
    out = maker_economics(frame)
    # NO entry = 97c, no fee for non-maker-fee series
    assert out["maker_entry_cents"].to_list() == [97.0, 97.0]
    win, loss = out["maker_hold_return"].to_list()
    assert abs(win - 3 / 97) < 1e-9      # collect 3c on 97c
    assert abs(loss - (-1.0)) < 1e-9     # tail fired: lose everything


def test_maker_economics_charges_maker_fee_only_on_quadratic_maker_series():
    frame = pl.DataFrame({
        "side": ["no"],
        "yes_price_cents": [3],
        "fee_type": ["quadratic_with_maker_fees"],
        "result_yes": [0],
        "hold_seconds": [86400],
    })
    out = maker_economics(frame)
    # fee = ceil(1.75% * 3 * 97 / 100) = ceil(0.051) = 1c
    assert abs(out["maker_hold_return"][0] - (3 - 1) / 97) < 1e-9
