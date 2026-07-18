import datetime as dt

import polars as pl
import pytest

from kalshi_data.analysis.weather_alpha import (
    attach_rolling_calibration,
    probability_yes,
)
from kalshi_data.features.weather import (
    aggregate_previous_run_payload,
    event_target_date,
)


UTC = dt.timezone.utc


def test_event_target_date_parses_old_and_kx_tickers():
    assert event_target_date("HIGHNY-23JAN09") == dt.date(2023, 1, 9)
    assert event_target_date("KXHIGHCHI-26JUL18") == dt.date(2026, 7, 18)
    assert event_target_date("KXCITIESWEATHER-25JAN03(CHI)(NY)") is None
    assert event_target_date("KXNOTADATE-26MAY47") is None


def test_previous_run_daily_feature_is_available_only_after_every_hour_was_published():
    payload = {
        "hourly": {
            "time": [f"2025-01-02T{hour:02d}:00" for hour in range(24)],
            "temperature_2m_previous_day2": [float(hour) for hour in range(24)],
        }
    }

    rows = aggregate_previous_run_payload(
        payload,
        station="nyc-central-park",
        timezone="America/New_York",
        retrieved_at=dt.datetime(2026, 7, 18, tzinfo=UTC),
    )

    high = next(row for row in rows if row["metric"] == "daily_max_temperature_f")
    low = next(row for row in rows if row["metric"] == "daily_min_temperature_f")
    assert high["value"] == "23.000"
    assert low["value"] == "0.000"
    # The 23:00 valid hour, forecast two days earlier, plus a conservative
    # six-hour model-publication lag controls availability of the daily value.
    assert high["available_at"] == dt.datetime(2025, 1, 1, 10, tzinfo=UTC)


def test_rolling_calibration_never_uses_observation_unavailable_at_forecast_time():
    forecasts = pl.DataFrame({
        "station": ["a", "a"],
        "weather_stat": ["high", "high"],
        "target_date": [dt.date(2025, 1, 1), dt.date(2025, 1, 2)],
        "lead_days": [1, 1],
        "forecast_f": [50.0, 60.0],
        "available_at": [
            dt.datetime(2024, 12, 31, tzinfo=UTC),
            dt.datetime(2025, 1, 1, 12, tzinfo=UTC),
        ],
    })
    observations = pl.DataFrame({
        "station": ["a", "a"],
        "weather_stat": ["high", "high"],
        "target_date": [dt.date(2025, 1, 1), dt.date(2025, 1, 2)],
        "observed_f": [55.0, 80.0],
        "available_at": [
            dt.datetime(2025, 1, 3, tzinfo=UTC),
            dt.datetime(2025, 1, 4, tzinfo=UTC),
        ],
    })

    out = attach_rolling_calibration(forecasts, observations, minimum_history=1)

    assert out["calibration_n"].to_list() == [None, None]


def test_rolling_calibration_is_station_specific():
    forecasts = pl.DataFrame({
        "station": ["a", "b", "a", "b"],
        "weather_stat": ["high"] * 4,
        "target_date": [
            dt.date(2025, 1, 1), dt.date(2025, 1, 1),
            dt.date(2025, 1, 4), dt.date(2025, 1, 4),
        ],
        "lead_days": [1] * 4,
        "forecast_f": [50.0, 50.0, 60.0, 60.0],
        "available_at": [
            dt.datetime(2024, 12, 31, tzinfo=UTC),
            dt.datetime(2024, 12, 31, tzinfo=UTC),
            dt.datetime(2025, 1, 3, 12, tzinfo=UTC),
            dt.datetime(2025, 1, 3, 12, tzinfo=UTC),
        ],
    })
    observations = pl.DataFrame({
        "station": ["a", "b", "a", "b"],
        "weather_stat": ["high"] * 4,
        "target_date": [
            dt.date(2025, 1, 1), dt.date(2025, 1, 1),
            dt.date(2025, 1, 4), dt.date(2025, 1, 4),
        ],
        "observed_f": [60.0, 40.0, 70.0, 50.0],
        "available_at": [
            dt.datetime(2025, 1, 3, tzinfo=UTC),
            dt.datetime(2025, 1, 3, tzinfo=UTC),
            dt.datetime(2025, 1, 6, tzinfo=UTC),
            dt.datetime(2025, 1, 6, tzinfo=UTC),
        ],
    })

    out = attach_rolling_calibration(forecasts, observations, minimum_history=1)
    later = out.filter(pl.col("target_date") == dt.date(2025, 1, 4)).sort("station")

    assert later["calibration_bias_f"].to_list() == [10.0, -10.0]


@pytest.mark.parametrize(
    ("strike_type", "floor", "cap", "expected"),
    [
        ("greater", 70.0, None, 0.5),
        ("less", None, 71.0, 0.5),
        ("between", 70.0, 71.0, pytest.approx(0.6826895, abs=1e-6)),
    ],
)
def test_probability_yes_respects_integer_temperature_rule_boundaries(
    strike_type, floor, cap, expected
):
    assert probability_yes(strike_type, floor, cap, mean=70.5, sigma=1.0) == expected
