"""Order-book snapshot recorder - the one dataset that cannot be backfilled.

Each run: refresh the list of open deployment-tier markets (cached for the
day), then record top-of-book levels for every one of them, appended to
data/books/books_YYYYMMDD.jsonl. Scheduled several times daily via launchd.

Scope note: deployment tier only, by design - depth in the instrumentation
tier is not an input to any decision this plan makes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json

import polars as pl

from ..core.client import KalshiClient

from ..core.paths import BOOKS as BOOKS_DIR, SERIES

CACHE = BOOKS_DIR / "open_markets_cache.json"
LEVELS = 5


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def open_deployment_markets(client: KalshiClient) -> list[str]:
    today = _utc_now().date().isoformat()
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
        if cache.get("date") == today:
            return cache["tickers"]
    series = pl.read_parquet(SERIES).filter(pl.col("tier") == "deployment")
    tickers: list[str] = []
    for s in series.iter_rows(named=True):
        for page in client.paginate("/markets", "markets", status="open", series_ticker=s["ticker"]):
            tickers.extend(m["ticker"] for m in page if m.get("ticker"))
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"date": today, "tickers": tickers}))
    return tickers


def top_levels(book: dict, side: str) -> list[list[str]]:
    levels = book.get(f"{side}_dollars") or book.get(side) or []
    return levels[-LEVELS:] if levels else []


def run_once(limit: int | None = None, rps: float = 8.0) -> None:
    client = KalshiClient(rps=rps)
    tickers = open_deployment_markets(client)
    if limit:
        tickers = tickers[:limit]
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BOOKS_DIR / f"books_{_utc_now():%Y%m%d}.jsonl"
    written, errors = 0, 0
    with out_path.open("a") as f:
        for ticker in tickers:
            try:
                resp = client.get(f"/markets/{ticker}/orderbook", depth=LEVELS)
            except Exception:
                errors += 1
                continue
            book = resp.get("orderbook_fp") or resp.get("orderbook") or {}
            rec = {
                "ts": _utc_now().isoformat(timespec="seconds"),
                "ticker": ticker,
                "yes": top_levels(book, "yes"),
                "no": top_levels(book, "no"),
            }
            f.write(json.dumps(rec) + "\n")
            written += 1
    print(f"recorder: {written:,} books written, {errors} errors -> {out_path.name}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--rps", type=float, default=8.0)
    args = ap.parse_args()
    run_once(limit=args.limit, rps=args.rps)
