from kalshi_data.ingest.market_metadata import fetch_series_metadata, metadata_row


def test_metadata_row_preserves_ladder_and_rule_fields():
    row = metadata_row({
        "ticker": "M", "event_ticker": "E", "title": "Above 100?",
        "yes_sub_title": "100 or above", "no_sub_title": "Below 100",
        "floor_strike": 100.0, "cap_strike": None, "strike_type": "greater",
        "rules_primary": "If the value is above 100", "rules_secondary": "Official source",
        "settlement_ts": "2026-01-01T00:00:00Z",
    }, {"ticker": "S", "category": "Economics", "tier": "deployment"})
    assert row["series_ticker"] == "S"
    assert row["floor_strike"] == 100.0
    assert row["yes_sub_title"] == "100 or above"
    assert row["rules_primary"].startswith("If the value")
    assert row["settled_time"] == "2026-01-01T00:00:00Z"


def test_fetch_series_metadata_combines_historical_and_live_without_duplicates():
    class Client:
        def paginate(self, path, key, **params):
            assert params == {"status": "settled", "series_ticker": "S"}
            base = {"ticker": "M", "event_ticker": "E", "title": path}
            yield [base]

    rows = fetch_series_metadata(
        Client(), {"ticker": "S", "category": "Economics", "tier": "deployment"}
    )
    assert len(rows) == 1
    assert rows[0]["ticker"] == "M"
