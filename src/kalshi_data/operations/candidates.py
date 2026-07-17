"""Daily candidate list: open markets matching the qualifying cells.

Pipeline (market-structure.md Part 2 + rulebook-sweep selection rules):
  1. open markets in Politics / Financials deployment series
  2. entry window: Politics 20-45d to close; Financials 60-120d
  3. YES price band (from live book): Politics ask <= 5c; Financials ask <= 10c
  4. exclusions: RED rulebooks, ticket-price series, professionally-priced list
  5. emit: ticker, days, suggested NO rest price (= 100 - yes_ask, joining the
     bid), volume, and rulebook verdict if swept
"""

from __future__ import annotations

import datetime as dt
import json

import polars as pl

from ..core.client import KalshiClient
from ..core.parse import cents

from ..core.paths import CANDIDATES, REPORTS as REPORTS_DIR, RULEBOOK_VERDICTS, SERIES

STRUCTURAL_EXCLUSIONS = {
    "KXRTICKET", "KXDTICKET", "KXWCPRICE", "KXNHLPRICE", "KXNBAFINALSPRICE",  # tickets
    "KXFED", "KXFEDDECISION", "KXPAYROLLS", "KXGDP",             # professionally priced
}
VERDICTS: dict = json.loads(RULEBOOK_VERDICTS.read_text())
GREEN = {t for t, v in VERDICTS.items() if v["verdict"] == "GREEN"}
YELLOW = {t for t, v in VERDICTS.items() if v["verdict"] == "YELLOW"}
RED = {t for t, v in VERDICTS.items() if v["verdict"] == "RED"}
BLACKLIST = RED | STRUCTURAL_EXCLUSIONS

CELLS = {
    "Politics": {"window": (20, 45), "max_ask": 5},
    "Financials": {"window": (60, 120), "max_ask": 10},
}

CANDIDATE_COLUMNS = [
    "category",
    "series",
    "ticker",
    "title",
    "days_to_close",
    "yes_ask_c",
    "rest_no_at_c",
    "volume",
    "rulebook",
]

CANDIDATE_SCHEMA = {
    "category": pl.String,
    "series": pl.String,
    "ticker": pl.String,
    "title": pl.String,
    "days_to_close": pl.Int64,
    "yes_ask_c": pl.Int64,
    "rest_no_at_c": pl.Int64,
    "volume": pl.Float64,
    "rulebook": pl.String,
}


def run(rps: float = 9.0) -> pl.DataFrame:
    series = pl.read_parquet(SERIES).filter(
        (pl.col("tier") == "deployment") & pl.col("category").is_in(list(CELLS))
    )
    client = KalshiClient(rps=rps)
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for s in series.iter_rows(named=True):
        if s["ticker"] in BLACKLIST:
            continue
        cell = CELLS[s["category"]]
        for page in client.paginate("/markets", "markets", status="open", series_ticker=s["ticker"]):
            for m in page:
                ask = cents(m, "yes_ask")
                close = m.get("close_time")
                if not ask or not close or not (1 <= ask <= cell["max_ask"]):
                    continue
                days = (dt.datetime.fromisoformat(close.replace("Z", "+00:00")) - now).days
                if not (cell["window"][0] <= days <= cell["window"][1]):
                    continue
                verdict = "GREEN" if s["ticker"] in GREEN else "YELLOW" if s["ticker"] in YELLOW else "UNSWEPT"
                rows.append(
                    {
                        "category": s["category"],
                        "series": s["ticker"],
                        "ticker": m["ticker"],
                        "title": (m.get("title") or s["title"] or "")[:60],
                        "days_to_close": days,
                        "yes_ask_c": ask,
                        "rest_no_at_c": 100 - ask,
                        "volume": m.get("volume") or 0,
                        "rulebook": verdict,
                    }
                )
    df = (
        pl.DataFrame(rows).select(CANDIDATE_COLUMNS).sort(["category", "days_to_close"])
        if rows
        else pl.DataFrame(schema=CANDIDATE_SCHEMA)
    )
    REPORTS_DIR.mkdir(exist_ok=True)
    stamp = f"{now:%Y-%m-%d}"
    lines = [f"# Candidate list — {stamp}", "",
             f"{len(df)} candidates (GREEN {len(df.filter(pl.col('rulebook')=='GREEN'))}, "
             f"YELLOW {len(df.filter(pl.col('rulebook')=='YELLOW'))}, "
             f"UNSWEPT {len(df.filter(pl.col('rulebook')=='UNSWEPT'))})", ""]
    cols = df.columns
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "---|" * len(cols))
    for row in df.iter_rows():
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    (REPORTS_DIR / "candidates_today.md").write_text("\n".join(lines))
    df.write_json(CANDIDATES)
    print(f"candidates: {len(df)} -> reports/candidates_today.md + data/candidates_today.json")
    return df


if __name__ == "__main__":
    run()
