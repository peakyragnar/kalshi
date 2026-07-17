"""SEC EDGAR registration-filing features for IPO candidate markets.

The live adapter stores observations only. It does not annotate orders or turn
the absence of a search match into a safe/clear trading signal.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
from urllib.parse import urljoin

import httpx
import polars as pl

from .store import normalize_features, write_partition
from ..core.paths import CANDIDATES, FEATURES, REPORTS


SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
ARCHIVES = "https://www.sec.gov"
HEADERS = {
    "User-Agent": "kalshi-structure-research/0.1 (point-in-time academic research)",
    "Accept-Encoding": "gzip, deflate",
}
IPO_TITLE = re.compile(
    r"^When will (.+?)(?: officially announce an)? IPO\?*$", re.IGNORECASE
)
FORMS = {"S-1", "S-1/A", "F-1", "F-1/A"}


def ipo_company(title: str) -> str | None:
    match = IPO_TITLE.match(title.strip())
    return match.group(1).strip() if match else None


def _hits(payload: dict) -> list[dict]:
    return [h.get("_source") or {} for h in ((payload.get("hits") or {}).get("hits") or [])]


def _text(value: object) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value) if value is not None else ""


def filing_feature(
    entity: str, company: str, payload: dict, checked: dt.datetime
) -> dict:
    candidates = [h for h in _hits(payload) if h.get("form") in FORMS and h.get("file_date")]
    candidates = [
        h for h in candidates
        if dt.date.fromisoformat(h["file_date"]) <= checked.date()
    ]
    candidates.sort(key=lambda h: (h["file_date"], h.get("form", "")), reverse=True)
    if candidates:
        hit = candidates[0]
        filed = dt.datetime.combine(
            dt.date.fromisoformat(hit["file_date"]), dt.time(), tzinfo=dt.timezone.utc
        )
        # Search results expose date but not acceptance time. Make the feature
        # available next UTC day so a same-day backtest cannot see it early.
        available = min(filed + dt.timedelta(days=1), checked)
        link = urljoin(ARCHIVES, hit.get("link_to_filing_details") or "")
        file_number = _text(hit.get("file_num")) or "?"
        evidence = (
            f"{company}; form {hit.get('form')}; file {file_number}; "
            f"filed {hit['file_date']}; {link}"
        )
        value = f"FILED:{hit['form']}"
        revision = file_number if file_number != "?" else f"{hit['form']}:{hit['file_date']}"
        effective = filed
    else:
        value = "NO_MATCH"
        evidence = f"No S-1/F-1 registration filing returned for exact query '{company}'; absence is not a CLEAR signal"
        revision = checked.date().isoformat()
        effective = checked
        available = checked
    return {
        "source": "sec-edgar-efts",
        "entity": entity,
        "metric": "ipo_registration_status",
        "effective_at": effective,
        "available_at": available,
        "retrieved_at": checked,
        "value": value,
        "revision": revision,
        "evidence": evidence,
    }


def fetch_company(company: str, client: httpx.Client | None = None) -> dict:
    client = client or httpx.Client(timeout=30, headers=HEADERS, follow_redirects=True)
    response = client.get(
        SEARCH_URL,
        params={"q": f'"{company}"', "forms": "S-1,S-1/A,F-1,F-1/A", "from": 0, "size": 20},
    )
    response.raise_for_status()
    return response.json()


def run() -> None:
    candidates = json.loads(CANDIDATES.read_text())
    targets = [(c["ticker"], ipo_company(c.get("title", ""))) for c in candidates]
    targets = [(ticker, company) for ticker, company in targets if company]
    if not targets:
        print("EDGAR: no IPO candidates")
        return
    checked = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    client = httpx.Client(timeout=30, headers=HEADERS, follow_redirects=True)
    cache: dict[str, dict] = {}
    rows = []
    for ticker, company in targets:
        if company not in cache:
            try:
                cache[company] = fetch_company(company, client)
            except Exception as exc:
                cache[company] = {"error": str(exc)}
            time.sleep(0.11)
        payload = cache[company]
        if "error" in payload:
            rows.append({
                "source": "sec-edgar-efts", "entity": ticker,
                "metric": "ipo_registration_status", "effective_at": checked,
                "available_at": checked, "retrieved_at": checked, "value": "UNKNOWN",
                "revision": checked.date().isoformat(),
                "evidence": f"EDGAR query failed for {company}: {payload['error']}",
            })
        else:
            rows.append(filing_feature(ticker, company, payload, checked))
    frame = normalize_features(pl.DataFrame(rows))
    path = FEATURES / f"sec-edgar-efts-{checked:%Y%m%d}.parquet"
    write_partition(frame, path)
    report = [f"# EDGAR IPO features — {checked.date()}", ""]
    for row in frame.iter_rows(named=True):
        report.append(f"- **{row['value']}** {row['entity']} — {row['evidence']}")
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "edgar_features.md").write_text("\n".join(report) + "\n")
    print(f"EDGAR: {len(frame)} candidate observations -> {path}")


if __name__ == "__main__":
    run()
