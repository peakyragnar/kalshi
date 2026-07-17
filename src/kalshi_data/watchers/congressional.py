"""Congressional calendar watcher: tail signals for confirmation-type markets.

The institutional fact this exploits: a nominee cannot be confirmed without
Senate floor time, and floor eligibility is published. The pipeline is
committee -> Executive Calendar -> (cloture) -> floor vote, each stage public.

Keyless sources (probed 2026-07-17):
  - Executive Calendar PDF: senate.gov/legislative/LIS/executive_calendar/xcalv.pdf
  - Session-days XML:       senate.gov/legislative/schedule/floor_schedule.xml

Signals (NO-seller's perspective; YES = confirmed by deadline):
  HOT     - name appears in the calendar's cloture section: vote imminent.
            Never place; flag resting orders.
  WARM    - name on the Executive Calendar: floor-eligible any session day.
  CLEAR   - name absent from the calendar: still in committee; confirmation
            requires calendaring first, which our daily cadence would catch.
  UNKNOWN - could not extract or match a name. Treated as WARM downstream,
            never as CLEAR (unknown is not safe).
"""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import xml.etree.ElementTree as ET

import httpx

from ..core.paths import CANDIDATES, REPORTS, TAIL_SIGNALS

CAL_PDF_URL = "https://www.senate.gov/legislative/LIS/executive_calendar/xcalv.pdf"
SESSION_XML_URL = "https://www.senate.gov/legislative/schedule/floor_schedule.xml"
HEADERS = {"User-Agent": "kalshi-structure-research/0.1"}

CONFIRMATION_TITLE = re.compile(r"^Will (.+?) be confirmed", re.IGNORECASE)


def extract_nominee(title: str) -> str | None:
    m = CONFIRMATION_TITLE.match(title.strip())
    if not m:
        return None
    name = re.sub(r'["“”].*?["“”]', " ", m.group(1))  # drop nicknames
    name = re.sub(r"\s+", " ", name).strip()
    return name or None


def last_name(name: str) -> str:
    return name.split()[-1]


def fetch_calendar_text() -> str:
    from pypdf import PdfReader

    r = httpx.get(CAL_PDF_URL, timeout=30, headers=HEADERS, follow_redirects=True)
    r.raise_for_status()
    reader = PdfReader(io.BytesIO(r.content))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def fetch_session_days() -> list[dt.date]:
    r = httpx.get(SESSION_XML_URL, timeout=30, headers=HEADERS, follow_redirects=True)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    days = []
    for el in root.iter("LegislativeDay"):
        raw = el.get("LegislativeDayDate", "")
        try:
            days.append(dt.datetime.fromisoformat(raw).date())
        except ValueError:
            continue
    return sorted(set(days))


def session_days_before(deadline: dt.date, days: list[dt.date]) -> int | None:
    """None when the feed carries no future days (it records past convenings)."""
    today = dt.date.today()
    if not days or max(days) < today:
        return None
    return sum(1 for d in days if today <= d < deadline)


def evidence(nominee: str | None, cal_text: str, sig: str) -> str:
    """Human-readable why: the exact calendar text behind the signal."""
    if sig == "UNKNOWN":
        return "calendar unavailable or nominee name not extractable from the market title"
    surname = last_name(nominee)
    if sig == "CLEAR":
        return f"'{surname}' does not appear anywhere in the current Executive Calendar"
    m = re.search(rf".{{0,90}}\b{re.escape(surname)}\b.{{0,110}}", cal_text, re.DOTALL)
    snippet = re.sub(r"\s+", " ", m.group(0)).strip() if m else surname
    prefix = "in the CLOTURE section: " if sig == "HOT" else "on the Executive Calendar: "
    return prefix + "…" + snippet + "…"


def signal(nominee: str | None, cal_text: str) -> str:
    if not nominee or not cal_text:
        return "UNKNOWN"
    surname = last_name(nominee)
    if not re.search(rf"\b{re.escape(surname)}\b", cal_text):
        return "CLEAR"
    cloture = cal_text.lower().find("cloture")
    if cloture >= 0:
        section = cal_text[cloture: cloture + 4000]
        if re.search(rf"\b{re.escape(surname)}\b", section):
            return "HOT"
    return "WARM"


def run() -> None:
    cands = json.loads(CANDIDATES.read_text())
    targets = [c for c in cands if extract_nominee(c["title"])]
    if not targets:
        print("watcher: no confirmation-type candidates today")
        return
    cal_text = ""
    try:
        cal_text = fetch_calendar_text()
    except Exception as e:
        print(f"watcher: calendar fetch failed ({e}); all signals UNKNOWN")
    try:
        sess = fetch_session_days()
    except Exception:
        sess = []

    lines = [f"# Tail signals — {dt.date.today()}", ""]
    records = []
    checked = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for c in targets:
        nominee = extract_nominee(c["title"])
        sig = signal(nominee, cal_text)
        ev = evidence(nominee, cal_text, sig)
        c["tail_signal"] = sig
        deadline = dt.date.today() + dt.timedelta(days=int(c["days_to_close"]))
        nsess = session_days_before(deadline, sess) if sess else None
        c["session_days_left"] = nsess
        records.append(
            {
                "ticker": c["ticker"],
                "title": c["title"],
                "nominee": nominee,
                "signal": sig,
                "evidence": ev,
                "session_days_left": nsess,
                "checked": checked,
                "source": CAL_PDF_URL,
            }
        )
        lines.append(
            f"- **{sig}** {c['ticker']} — {nominee} "
            f"({nsess if nsess is not None else '?'} session days before deadline)\n"
            f"  - {ev}"
        )
    CANDIDATES.write_text(json.dumps(cands))
    TAIL_SIGNALS.write_text(json.dumps(records, indent=1))
    (REPORTS / "tail_signals.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    run()
