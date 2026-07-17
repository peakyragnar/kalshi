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
