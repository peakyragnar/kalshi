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


def open_deployment_markets(client: KalshiClient) -> dict[str, str | None]:
    """Open deployment-tier tickers -> close_time (ISO string or None), cached daily."""
    today = _utc_now().date().isoformat()
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
        if cache.get("date") == today and "markets" in cache:
            return cache["markets"]
    series = pl.read_parquet(SERIES).filter(pl.col("tier") == "deployment")
    markets: dict[str, str | None] = {}
    for s in series.iter_rows(named=True):
        for page in client.paginate("/markets", "markets", status="open", series_ticker=s["ticker"]):
            for m in page:
                if m.get("ticker"):
                    markets[m["ticker"]] = m.get("close_time")
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"date": today, "markets": markets}))
    return markets


def near_close(markets: dict[str, str | None], hours: float, now: dt.datetime | None = None) -> list[str]:
    """Tickers closing within `hours` — the final-hours capture window
    (03-information-edge-plan.md Track B: fill-rate gate + decay early warning)."""
    now = now or _utc_now()
    horizon = now + dt.timedelta(hours=hours)
    out = []
    for ticker, close in markets.items():
        if not close:
            continue
        try:
            close_at = dt.datetime.fromisoformat(close.replace("Z", "+00:00"))
        except ValueError:
            continue
        if now < close_at <= horizon:
            out.append(ticker)
    return out


def top_levels(book: dict, side: str) -> list[list[str]]:
    levels = book.get(f"{side}_dollars") or book.get(side) or []
    return levels[-LEVELS:] if levels else []


def run_once(limit: int | None = None, rps: float = 8.0, near_close_hours: float | None = None) -> None:
    client = KalshiClient(rps=rps)
    markets = open_deployment_markets(client)
    tickers = near_close(markets, near_close_hours) if near_close_hours else list(markets)
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
    ap.add_argument("--near-close", type=float, default=None, metavar="HOURS",
                    help="restrict to markets closing within HOURS (final-hours capture)")
    args = ap.parse_args()
    run_once(limit=args.limit, rps=args.rps, near_close_hours=args.near_close)
