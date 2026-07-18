import polars as pl

from kalshi_data.ingest.market_metadata import (
    fetch_market_metadata,
    fetch_series_metadata,
    metadata_gaps,
    metadata_row,
    normalize_metadata_frame,
)


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


def test_ticker_repair_falls_back_between_live_and_historical_endpoints():
    class Client:
        def get(self, path):
            if path.startswith("/markets/"):
                raise RuntimeError("not live")
            return {"market": {"ticker": "M", "event_ticker": "E", "title": "Recovered"}}

    row = fetch_market_metadata(
        Client(), "M", {"ticker": "S", "category": "Economics", "tier": "deployment"}
    )
    assert row["ticker"] == "M"
    assert row["title"] == "Recovered"


def test_metadata_shards_normalize_integer_strikes_to_float_schema():
    row = metadata_row(
        {"ticker": "M", "floor_strike": 1, "cap_strike": 2},
        {"ticker": "S", "category": "Economics", "tier": "deployment"},
    )
    frame = normalize_metadata_frame([row])
    assert frame.schema["floor_strike"] == pl.Float64
    assert frame.schema["cap_strike"] == pl.Float64


def test_ticker_gap_repair_only_selects_current_deployment_series():
    raw = pl.DataFrame({
        "ticker": ["DEPLOY-M", "SPORT-M"],
        "series_ticker": ["DEPLOY", "SPORT"],
    })
    stored = pl.DataFrame({"ticker": []}, schema={"ticker": pl.String})
    deployment_series = pl.DataFrame({
        "ticker": ["DEPLOY"], "category": ["Economics"], "tier": ["deployment"]
    })

    gaps = metadata_gaps(raw, stored, deployment_series)

    assert gaps["ticker"].to_list() == ["DEPLOY-M"]
