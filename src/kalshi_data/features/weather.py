"""Point-in-time daily temperature forecasts and settlement-station observations."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import datetime as dt
import re
import time
from zoneinfo import ZoneInfo

import httpx
import polars as pl

from .store import normalize_features, write_partition
from ..core.paths import (
    DECISION_POINTS,
    WEATHER_FORECASTS,
    WEATHER_OBSERVATIONS,
)


PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
NCEI_DAILY_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
MODEL_PUBLICATION_LAG = dt.timedelta(hours=6)
MONTHS = {
    name: number for number, name in enumerate(
        ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"),
        start=1,
    )
}
EVENT_DATE = re.compile(r"-(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})$")


@dataclass(frozen=True)
class Station:
    key: str
    latitude: float
    longitude: float
    timezone: str
    ncei_id: str
    series: tuple[str, ...]


STATIONS = (
    Station("nyc-central-park", 40.7789, -73.9692, "America/New_York", "USW00094728", ("KXHIGHNY", "KXLOWTNYC")),
    Station("chicago-midway", 41.7868, -87.7522, "America/Chicago", "USW00014819", ("KXHIGHCHI", "KXLOWTCHI")),
    Station("austin-bergstrom", 30.1975, -97.6664, "America/Chicago", "USW00013904", ("KXHIGHAUS", "KXLOWTAUS")),
    Station("miami-international", 25.7959, -80.2870, "America/New_York", "USW00012839", ("KXHIGHMIA", "KXLOWTMIA")),
    Station("denver-international", 39.8561, -104.6737, "America/Denver", "USW00003017", ("KXHIGHDEN", "KXLOWTDEN")),
    Station("philadelphia-international", 39.8744, -75.2424, "America/New_York", "USW00013739", ("KXHIGHPHIL", "KXLOWTPHIL")),
    Station("los-angeles-international", 33.9416, -118.4085, "America/Los_Angeles", "USW00023174", ("KXHIGHLAX", "KXLOWTLAX")),
    Station("seattle-tacoma", 47.4502, -122.3088, "America/Los_Angeles", "USW00024233", ("KXHIGHTSEA", "KXLOWTSEA")),
    Station("san-francisco-international", 37.6213, -122.3790, "America/Los_Angeles", "USW00023234", ("KXHIGHTSFO", "KXLOWTSFO")),
    Station("phoenix-sky-harbor", 33.4342, -112.0116, "America/Phoenix", "USW00023183", ("KXHIGHTPHX", "KXLOWTPHX")),
    Station("minneapolis-st-paul", 44.8848, -93.2223, "America/Chicago", "USW00014922", ("KXHIGHTMIN",)),
    Station("oklahoma-city-will-rogers", 35.3931, -97.6007, "America/Chicago", "USW00013967", ("KXHIGHTOKC", "KXLOWTOKC")),
    Station("dallas-love-field", 32.8471, -96.8518, "America/Chicago", "USW00013960", ("KXHIGHTDAL", "KXLOWTDAL")),
    Station("san-antonio-international", 29.5337, -98.4698, "America/Chicago", "USW00012921", ("KXHIGHTSATX", "KXLOWTSATX")),
    Station("houston-hobby", 29.6454, -95.2789, "America/Chicago", "USW00012918", ("KXHIGHHOU", "KXHIGHTHOU", "KXLOWTHOU")),
    Station("washington-reagan", 38.8512, -77.0402, "America/New_York", "USW00013743", ("KXLOWTDC",)),
    Station("new-orleans-international", 29.9934, -90.2580, "America/Chicago", "USW00012916", ("KXLOWTNOLA",)),
    Station("las-vegas-harry-reid", 36.0840, -115.1537, "America/Los_Angeles", "USW00023169", ("KXHIGHTLV", "KXLOWTLV")),
    Station("boston-logan", 42.3656, -71.0096, "America/New_York", "USW00014739", ("KXLOWTBOS",)),
    Station("atlanta-hartsfield", 33.6407, -84.4277, "America/New_York", "USW00013874", ("KXLOWTATL",)),
)
SERIES_TO_STATION = {
    series: station for station in STATIONS for series in station.series
}


def event_target_date(event_ticker: str | None) -> dt.date | None:
    match = EVENT_DATE.search(event_ticker or "")
    if not match:
        return None
    year, month, day = match.groups()
    try:
        return dt.date(2000 + int(year), MONTHS[month], int(day))
    except ValueError:
        return None


def aggregate_previous_run_payload(
    payload: dict, station: str, timezone: str, retrieved_at: dt.datetime
) -> list[dict]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    zone = ZoneInfo(timezone)
    rows = []
    for variable, values in hourly.items():
        match = re.fullmatch(r"temperature_2m_previous_day(\d)", variable)
        if not match:
            continue
        lead = int(match.group(1))
        by_date: dict[dt.date, list[tuple[dt.datetime, float]]] = {}
        for raw_time, raw_value in zip(times, values):
            if raw_value is None:
                continue
            local = dt.datetime.fromisoformat(raw_time).replace(tzinfo=zone)
            by_date.setdefault(local.date(), []).append((local, float(raw_value)))
        for target_date, observations in by_date.items():
            latest_valid = max(item[0] for item in observations)
            available = (
                latest_valid - dt.timedelta(days=lead) + MODEL_PUBLICATION_LAG
            ).astimezone(dt.timezone.utc)
            effective = dt.datetime.combine(
                target_date, dt.time(12), tzinfo=zone
            ).astimezone(dt.timezone.utc)
            evidence = (
                f"Open-Meteo Previous Runs API mirror of NOAA NCEP GFS global; "
                f"fixed lead {lead}d; station={station}; target={target_date}"
            )
            for metric, value in (
                ("daily_max_temperature_f", max(item[1] for item in observations)),
                ("daily_min_temperature_f", min(item[1] for item in observations)),
            ):
                rows.append({
                    "source": "open-meteo-noaa-gfs-previous-runs",
                    "entity": f"{station}:{target_date}",
                    "metric": metric,
                    "effective_at": effective,
                    "available_at": available,
                    "retrieved_at": retrieved_at,
                    "value": f"{value:.3f}",
                    "revision": f"gfs_global:lead{lead}",
                    "evidence": evidence,
                })
    return rows


def _json(client: httpx.Client, url: str, params: dict) -> dict | list:
    for attempt in range(5):
        response = client.get(url, params=params)
        if response.status_code not in {429, 500, 502, 503, 504}:
            response.raise_for_status()
            return response.json()
        time.sleep(2**attempt)
    response.raise_for_status()
    raise RuntimeError("unreachable")


def _forecast_year(
    station: Station, year: int, start: dt.date, end: dt.date, retrieved_at: dt.datetime
) -> list[dict]:
    with httpx.Client(timeout=120, headers={"User-Agent": "kalshi-structure-research/0.1"}) as client:
        payload = _json(client, PREVIOUS_RUNS_URL, {
            "latitude": station.latitude,
            "longitude": station.longitude,
            "start_date": max(start, dt.date(year, 1, 1)).isoformat(),
            "end_date": min(end, dt.date(year, 12, 31)).isoformat(),
            "hourly": ",".join(f"temperature_2m_previous_day{i}" for i in range(1, 8)),
            "temperature_unit": "fahrenheit",
            "timezone": station.timezone,
            "models": "gfs_global",
        })
    return aggregate_previous_run_payload(payload, station.key, station.timezone, retrieved_at)


def _observation_rows(
    station: Station, start: dt.date, end: dt.date, retrieved_at: dt.datetime
) -> list[dict]:
    with httpx.Client(timeout=120, headers={"User-Agent": "kalshi-structure-research/0.1"}) as client:
        payload = _json(client, NCEI_DAILY_URL, {
            "dataset": "daily-summaries",
            "stations": station.ncei_id,
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "format": "json",
            "units": "standard",
            "includeAttributes": "false",
        })
    zone = ZoneInfo(station.timezone)
    rows = []
    for raw in payload:
        target = dt.date.fromisoformat(raw["DATE"])
        available = dt.datetime.combine(
            target + dt.timedelta(days=2), dt.time(), tzinfo=zone
        ).astimezone(dt.timezone.utc)
        effective = dt.datetime.combine(target, dt.time(12), tzinfo=zone).astimezone(
            dt.timezone.utc
        )
        for field, metric in (
            ("TMAX", "observed_daily_max_temperature_f"),
            ("TMIN", "observed_daily_min_temperature_f"),
        ):
            if raw.get(field) in (None, ""):
                continue
            rows.append({
                "source": "noaa-ncei-daily-summaries",
                "entity": f"{station.key}:{target}",
                "metric": metric,
                "effective_at": effective,
                "available_at": available,
                "retrieved_at": retrieved_at,
                "value": f"{float(raw[field]):.3f}",
                "revision": f"{station.ncei_id}:{target}",
                "evidence": f"NOAA NCEI Daily Summaries station {station.ncei_id}",
            })
    return rows


def run(workers: int = 4) -> None:
    points = pl.read_parquet(DECISION_POINTS).select(
        "series_ticker", "event_ticker"
    ).unique()
    targets: dict[str, set[dt.date]] = {}
    for row in points.iter_rows(named=True):
        station = SERIES_TO_STATION.get(row["series_ticker"])
        target = event_target_date(row["event_ticker"])
        if station and target:
            targets.setdefault(station.key, set()).add(target)
    retrieved = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    tasks = []
    for station in STATIONS:
        dates = targets.get(station.key, set())
        if not dates:
            continue
        start, end = min(dates), max(dates)
        for year in range(start.year, end.year + 1):
            tasks.append(("forecast", station, year, start, end, dates))
        tasks.append(("observation", station, None, start, end, dates))
    forecast_rows, observation_rows = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for kind, station, year, start, end, dates in tasks:
            if kind == "forecast":
                future = pool.submit(_forecast_year, station, year, start, end, retrieved)
            else:
                future = pool.submit(_observation_rows, station, start, end, retrieved)
            futures[future] = (kind, station.key, dates)
        for index, future in enumerate(as_completed(futures), start=1):
            kind, key, dates = futures[future]
            rows = [
                row for row in future.result()
                if dt.date.fromisoformat(row["entity"].rsplit(":", 1)[1]) in dates
            ]
            (forecast_rows if kind == "forecast" else observation_rows).extend(rows)
            print(f"weather {index}/{len(futures)}: {kind} {key} ({len(rows):,} rows)", flush=True)
    forecasts = normalize_features(pl.DataFrame(forecast_rows, infer_schema_length=None))
    observations = normalize_features(pl.DataFrame(observation_rows, infer_schema_length=None))
    write_partition(forecasts, WEATHER_FORECASTS)
    write_partition(observations, WEATHER_OBSERVATIONS)
    print(
        f"weather: {len(forecasts):,} forecast features, "
        f"{len(observations):,} observations",
        flush=True,
    )


if __name__ == "__main__":
    run()
