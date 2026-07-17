from kalshi_data.core.parse import cents, market_row, quantity


def test_cents_prefers_integer_form():
    assert cents({"last_price": 42, "last_price_dollars": "0.9900"}, "last_price") == 42


def test_cents_falls_back_to_dollar_string():
    assert cents({"last_price_dollars": "0.8800"}, "last_price") == 88
    assert cents({}, "last_price") is None


def test_quantity_handles_fp_and_missing():
    assert quantity({"volume_fp": "123.00"}, "volume") == 123.0
    assert quantity({"volume": 5}, "volume") == 5.0
    assert quantity({}, "volume") is None


def test_market_row_joins_series_metadata():
    m = {
        "ticker": "KXCPI-26JUN-T-0.3",
        "event_ticker": "KXCPI-26JUN",
        "result": "no",
        "status": "settled",
        "close_time": "2026-07-14T12:25:00Z",
        "last_price_dollars": "0.0300",
    }
    s = {"ticker": "KXCPI", "category": "Economics", "tier": "deployment",
         "frequency": "monthly", "fee_type": "quadratic", "fee_multiplier": 1}
    row = market_row(m, s)
    assert row["series_ticker"] == "KXCPI"
    assert row["tier"] == "deployment"
    assert row["last_price_cents"] == 3
    assert row["result"] == "no"
