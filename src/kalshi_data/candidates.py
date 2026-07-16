"""Daily candidate list: open markets matching the qualifying cells.

Pipeline (market-structure.md Part 2 + rulebook-sweep selection rules):
  1. open markets in Politics / Financials deployment series
  2. entry window: Politics 20-45d to close; Financials 60-120d
  3. YES price band (from live book): Politics ask <= 5c; Financials ask <= 10c
  4. exclusions: RED rulebooks, ticket-price series, professionally-priced list
  5. emit: ticker, days, suggested NO rest price (= 100 - yes_ask, joining the
     bid), book depth at that level, rulebook verdict if swept
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from .client import KalshiClient
from .parse import cents

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

BLACKLIST = {
    "KXCRYPTOSTRUCTURE", "KXTARIFFCHECKS",                       # RED rulebooks
    "KXRTICKET", "KXDTICKET", "KXWCPRICE", "KXNHLPRICE", "KXNBAFINALSPRICE",  # tickets
    "KXFED", "KXFEDDECISION", "KXPAYROLLS", "KXGDP",             # professionally priced
}
GREEN = {
    "KXVISITVENEZUELA", "KXVISITIRAN", "KXVISITNYC", "KXTRUMPIRAN",
    "KXEXPELSWALWELLVOTES", "KXSAVEAMERICACLOTURE", "KXBILLSCOUNT",
    "KXAPRPOTUSEOY", "KXFTACOUNTRIES", "KXTRUMPPARDON", "KXLEAVEPOWELL",
    "KXLEAVEHOUSE", "KXNASDAQ100Y", "KXINXY", "KXTESLA", "KXTESLAPROD",
    "KXBOEING", "KXMETAHEADCOUNT", "KXSPOTIFYMAU", "KXCBVOLUME",
    "KXDASHORDERS", "KXUBERTRIPS",
}
YELLOW = {
    "KXPRESVISIT", "KXWHVISIT", "KXTARIFFRATECAN", "KXTARIFFRATEPRC",
    "KXLAGODAYS", "KXGOLDCARDS", "KXLEAVEADMIN", "KXRECESSAPPT",
    "KXIPO", "KXIPOANDURIL", "KXIPOSTARLINK", "KXNEWROLEX",
}

CELLS = {
    "Politics": {"window": (20, 45), "max_ask": 5},
    "Financials": {"window": (60, 120), "max_ask": 10},
}


def run(rps: float = 9.0) -> pl.DataFrame:
    series = pl.read_parquet(DATA_DIR / "series.parquet").filter(
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
    df = pl.DataFrame(rows).sort(["category", "days_to_close"])
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
    df.write_json(DATA_DIR / "candidates_today.json")
    print(f"candidates: {len(df)} -> reports/candidates_today.md + data/candidates_today.json")
    return df


if __name__ == "__main__":
    run()
