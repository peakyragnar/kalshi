import datetime as dt

import polars as pl
import pytest

from kalshi_data.features.store import asof_join, normalize_features, write_partition
from kalshi_data.features.edgar import filing_feature, ipo_company


UTC = dt.timezone.utc


def _feature(available_at, value="WARM"):
    return {
        "source": "senate-executive-calendar",
        "entity": "KXNOMINEE",
        "metric": "tail_signal",
        "effective_at": available_at,
        "available_at": available_at,
        "retrieved_at": available_at,
        "value": value,
        "revision": "current",
        "evidence": "calendar entry",
    }


def test_asof_join_never_uses_feature_published_after_decision():
    decision = dt.datetime(2026, 7, 17, 12, tzinfo=UTC)
    points = pl.DataFrame({"entity": ["KXNOMINEE"], "decision_time": [decision]})
    features = normalize_features(
        pl.DataFrame(
            [
                _feature(decision - dt.timedelta(hours=1), "CLEAR"),
                _feature(decision + dt.timedelta(hours=1), "HOT"),
            ]
        )
    )
    out = asof_join(points, features, metric="tail_signal")
    assert out.row(0, named=True)["feature_value"] == "CLEAR"


def test_invalid_feature_time_order_is_rejected():
    now = dt.datetime(2026, 7, 17, 12, tzinfo=UTC)
    bad = _feature(now)
    bad["retrieved_at"] = now - dt.timedelta(seconds=1)
    with pytest.raises(ValueError, match="retrieved_at"):
        normalize_features(pl.DataFrame([bad]))


def test_partition_rerun_is_idempotent(tmp_path):
    now = dt.datetime(2026, 7, 17, 12, tzinfo=UTC)
    df = normalize_features(pl.DataFrame([_feature(now)]))
    path = tmp_path / "features.parquet"
    write_partition(df, path)
    write_partition(df, path)
    assert len(pl.read_parquet(path)) == 1


def test_edgar_ipo_title_parser_handles_both_market_wordings():
    assert ipo_company("When will Glean IPO?") == "Glean"
    assert ipo_company("When will Databricks officially announce an IPO?") == "Databricks"
    assert ipo_company("Will CPI exceed 3%?") is None


def test_edgar_feature_uses_public_filing_timestamp_and_form():
    checked = dt.datetime(2026, 7, 17, 12, tzinfo=UTC)
    payload = {
        "hits": {"hits": [{"_source": {
            "file_date": "2026-07-16",
            "file_num": ["333-123"],
            "form": "S-1",
            "display_names": ["Glean Technologies, Inc."],
            "link_to_filing_details": "/Archives/edgar/data/1/x-index.html",
        }}]}
    }
    row = filing_feature("KXIPOGLEAN", "Glean", payload, checked)
    assert row["value"] == "FILED:S-1"
    # EFTS exposes only a filing date, not acceptance time. The adapter makes
    # it usable from the next UTC day to prevent same-day look-ahead.
    assert row["available_at"] == dt.datetime(2026, 7, 17, tzinfo=UTC)
    assert "333-123" in row["evidence"]
    assert row["revision"] == "333-123"


def test_same_day_edgar_observation_is_available_only_when_retrieved():
    checked = dt.datetime(2026, 7, 17, 12, tzinfo=UTC)
    payload = {"hits": {"hits": [{"_source": {
        "file_date": "2026-07-17", "file_num": "1", "form": "S-1"
    }}]}}
    row = filing_feature("M", "Company", payload, checked)
    assert row["available_at"] == checked
