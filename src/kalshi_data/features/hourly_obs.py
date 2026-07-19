"""Point-in-time hourly station observations -> running daily max/min.

Feeds weather-alpha v2's intraday requirement: a T-6h decision must know the
day so far, as the market does. Source: NCEI Global-Hourly (ISD) — actual
station METAR records, the same stations that settle the markets. Historical
backfill is legitimate point-in-time data because each observation is a
timestamped record; availability = observation time + a 1-hour transmission
allowance (METAR reaches public feeds within minutes; the hour is the
conservative reserve).

Rows land in the shared feature store as running aggregates per station-day:
metric running_daily_max_temperature_f / running_daily_min_temperature_f,
one row per hourly observation, available_at strictly increasing within the
day — so an as-of join at any decision time yields exactly what was knowable.
"""

from __future__ import annotations

import argparse
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from zoneinfo import ZoneInfo

import httpx
import polars as pl

from .store import normalize_features, write_partition
from .weather import STATIONS, Station
from ..core.paths import WEATHER_HOURLY_OBS

NCEI_HOURLY_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
TRANSMISSION_ALLOWANCE = dt.timedelta(hours=1)
QUALITY_REJECT = {"2", "3", "6", "7"}  # ISD suspect/erroneous quality codes


def parse_tmp(raw: str | None) -> float | None:
    """ISD TMP field: '+0261,1' -> 26.1C -> F. 9999 is missing."""
    if not raw:
        return None
    parts = raw.split(",")
    if len(parts) != 2 or parts[1] in QUALITY_REJECT:
        return None
    try:
        tenths_c = int(parts[0])
    except ValueError:
        return None
    if abs(tenths_c) >= 9999:
        return None
    return round(tenths_c / 10 * 9 / 5 + 32, 1)


def running_rows(
    station: Station, observations: list[dict], retrieved_at: dt.datetime
) -> list[dict]:
    """One feature row per observation carrying the running max/min so far
    that local calendar day. available_at = obs time + transmission allowance."""
    zone = ZoneInfo(station.timezone)
    parsed = []
    for record in observations:
        temp = parse_tmp(record.get("TMP"))
        if temp is None:
            continue
        try:
            when = dt.datetime.fromisoformat(record["DATE"]).replace(tzinfo=dt.timezone.utc)
        except (KeyError, ValueError):
            continue
        parsed.append((when, temp))
    parsed.sort()
    rows = []
    running: dict[dt.date, tuple[float, float]] = {}
    for when, temp in parsed:
        local_day = when.astimezone(zone).date()
        high, low = running.get(local_day, (temp, temp))
        high, low = max(high, temp), min(low, temp)
        running[local_day] = (high, low)
        available = (when + TRANSMISSION_ALLOWANCE).astimezone(dt.timezone.utc)
        effective = dt.datetime.combine(local_day, dt.time(12), tzinfo=zone).astimezone(dt.timezone.utc)
        for metric, value in (
            ("running_daily_max_temperature_f", high),
            ("running_daily_min_temperature_f", low),
        ):
            rows.append({
                "source": "ncei-global-hourly",
                "entity": f"{station.key}:{local_day}",
                "metric": metric,
                "effective_at": effective,
                "available_at": available,
                "retrieved_at": retrieved_at,
                "value": f"{value:.1f}",
                "revision": when.isoformat(timespec="seconds"),
                "evidence": f"ISD station {station.ncei_id} obs {when.isoformat(timespec='seconds')}",
            })
    return rows


def _fetch_station(
    station: Station, start: dt.date, end: dt.date, retrieved_at: dt.datetime
) -> list[dict]:
    with httpx.Client(timeout=180, headers={"User-Agent": "kalshi-structure-research/0.1"}) as client:
        response = client.get(NCEI_HOURLY_URL, params={
            "dataset": "global-hourly",
            "stations": station.ncei_id,
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dataTypes": "TMP",
            "format": "json",
        })
        response.raise_for_status()
        payload = response.json()
    return running_rows(station, payload, retrieved_at)


def run(start: str, end: str, workers: int = 4) -> None:
    start_date, end_date = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    retrieved = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    all_rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_fetch_station, station, start_date, end_date, retrieved): station.key
            for station in STATIONS
        }
        for index, future in enumerate(as_completed(futures), start=1):
            key = futures[future]
            try:
                rows = future.result()
            except Exception as error:
                print(f"hourly-obs {index}/{len(futures)}: {key} FAILED ({error})", flush=True)
                continue
            all_rows.extend(rows)
            print(f"hourly-obs {index}/{len(futures)}: {key} ({len(rows):,} rows)", flush=True)
    if not all_rows:
        print("hourly-obs: nothing fetched")
        return
    out = normalize_features(pl.DataFrame(all_rows, infer_schema_length=None))
    write_partition(out, WEATHER_HOURLY_OBS)
    print(f"hourly-obs: {len(out):,} feature rows -> {WEATHER_HOURLY_OBS.name}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    run(args.start, args.end, workers=args.workers)
