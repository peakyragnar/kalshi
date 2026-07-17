"""Congressional calendar watcher: tail signals for confirmation-type markets.

The institutional fact this exploits: a nominee cannot be confirmed without
Senate floor time, and floor eligibility is published. The pipeline is
committee -> Executive Calendar -> (cloture) -> floor vote, each stage public.

Keyless sources (probed 2026-07-17):
  - Executive Calendar PDF:  senate.gov/legislative/LIS/executive_calendar/xcalv.pdf
  - Tentative schedule XML:  senate.gov/legislative/{year}_schedule.xml
    (announced non-legislative periods; session days = weekdays outside them.
    floor_schedule.xml was abandoned: it records *past* convenings only.)

Name matching (calendar format: "Benjamin M. Flowers, of Ohio, to be ..."):
  A nominee counts as ON the calendar only when first and last name appear
  together (middle names/initials between them). A bare surname hit is
  explained away when it is mechanically attributable to someone else --
  a predecessor ("vice Clayton D. Johnson, term expired", lowercase "vice"
  only, so Vice Admirals stay matchable) or a senator ("Mr. Grassley").
  Explained mentions -> CLEAR; unexplained bare surnames -> UNKNOWN, never
  CLEAR (a formal first name can differ from the market title's).

Signals (NO-seller's perspective; YES = confirmed by deadline):
  HOT     - on the calendar AND surname in the cloture section (cloture
            entries abbreviate: "motion on the Flowers nomination").
            Never place; flag resting orders.
  WARM    - full name on the Executive Calendar: floor-eligible any session day.
  CLEAR   - not on the calendar: still in committee; confirmation requires
            calendaring first, which our daily cadence would catch.
  UNKNOWN - name not extractable, calendar unavailable, or ambiguous surname
            match. Treated as WARM downstream, never as CLEAR (unknown is
            not safe).
"""

from __future__ import annotations

import datetime as dt
import io
import json
import re
import xml.etree.ElementTree as ET

import httpx
import polars as pl

from ..core.paths import CANDIDATES, FEATURES, REPORTS, TAIL_SIGNALS
from ..features.store import normalize_features, write_partition

CAL_PDF_URL = "https://www.senate.gov/legislative/LIS/executive_calendar/xcalv.pdf"
SCHEDULE_XML_URL = "https://www.senate.gov/legislative/{year}_schedule.xml"
HEADERS = {"User-Agent": "kalshi-structure-research/0.1"}

CONFIRMATION_TITLE = re.compile(r"^Will (.+?) be confirmed", re.IGNORECASE)
GENERATIONAL_SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}

# a bare-surname mention attributable to someone other than the nominee:
# a predecessor clause ("vice <Full Name>," -- lowercase vice only) or a
# senator honorific ("Mr. Grassley") directly before the surname
EXPLAINED_BEFORE = re.compile(r"(?:\bvice\b[\s\S]{0,40}|\b(?:Mr|Mrs|Ms|Messrs|Mses)\.\s{0,3})$")

CLOTURE_SECTION_SPAN = 4000


def extract_nominee(title: str) -> str | None:
    m = CONFIRMATION_TITLE.match(title.strip())
    if not m:
        return None
    name = re.sub(r'["“”].*?["“”]', " ", m.group(1))  # drop nicknames
    name = re.sub(r"\s+", " ", name).strip()
    return name or None


def last_name(name: str) -> str:
    parts = [p for p in name.split() if p.lower() not in GENERATIONAL_SUFFIXES]
    return (parts or name.split())[-1]


def _full_name_re(nominee: str) -> re.Pattern | None:
    """First and last name within one entry's distance; None for single tokens."""
    first, last = nominee.split()[0], last_name(nominee)
    if first == last:
        return None
    return re.compile(rf"\b{re.escape(first)}\b[\s\S]{{0,40}}?\b{re.escape(last)}\b")


def _snip(text: str, start: int, end: int) -> str:
    return re.sub(r"\s+", " ", text[max(0, start - 90): end + 110]).strip()


def _cloture_hit(surname: str, cal_text: str) -> re.Match | None:
    c = cal_text.lower().find("cloture")
    if c < 0:
        return None
    section = cal_text[c: c + CLOTURE_SECTION_SPAN]
    m = re.search(rf"\b{re.escape(surname)}\b", section)
    return m if m else None


def assess(nominee: str | None, cal_text: str) -> tuple[str, str]:
    """(signal, evidence) -- evidence is the literal calendar text behind it."""
    if not nominee or not cal_text:
        return "UNKNOWN", "calendar unavailable or nominee name not extractable from the market title"
    surname = last_name(nominee)
    pat = _full_name_re(nominee)

    full = pat.search(cal_text) if pat else re.search(rf"\b{re.escape(surname)}\b", cal_text)
    if full:
        hit = _cloture_hit(surname, cal_text)
        if hit:
            c = cal_text.lower().find("cloture")
            section = cal_text[c: c + CLOTURE_SECTION_SPAN]
            return "HOT", "in the CLOTURE section: …" + _snip(section, hit.start(), hit.end()) + "…"
        return "WARM", "on the Executive Calendar: …" + _snip(cal_text, full.start(), full.end()) + "…"

    mentions = list(re.finditer(rf"\b{re.escape(surname)}\b", cal_text))
    if not mentions:
        return "CLEAR", f"'{surname}' does not appear anywhere in the current Executive Calendar"
    unexplained = [
        m for m in mentions if not EXPLAINED_BEFORE.search(cal_text[max(0, m.start() - 60): m.start()])
    ]
    if not unexplained:
        m = mentions[0]
        return "CLEAR", (
            f"'{surname}' appears only as a predecessor or senator reference, "
            f"not as a nominee: …{_snip(cal_text, m.start(), m.end())}…"
        )
    m = unexplained[0]
    return "UNKNOWN", (
        f"ambiguous: '{surname}' appears without '{nominee.split()[0]}' nearby — "
        f"possibly a different person, verify manually: …{_snip(cal_text, m.start(), m.end())}…"
    )


def signal(nominee: str | None, cal_text: str) -> str:
    return assess(nominee, cal_text)[0]


def fetch_calendar_text() -> str:
    from pypdf import PdfReader

    r = httpx.get(CAL_PDF_URL, timeout=30, headers=HEADERS, follow_redirects=True)
    r.raise_for_status()
    reader = PdfReader(io.BytesIO(r.content))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def parse_nonsession_ranges(content: bytes) -> list[tuple[dt.date, dt.date]]:
    root = ET.fromstring(content)
    out = []
    for d in root.iter("date"):
        try:
            out.append(
                (
                    dt.date.fromisoformat((d.findtext("beginDate") or "").strip()),
                    dt.date.fromisoformat((d.findtext("endDate") or "").strip()),
                )
            )
        except ValueError:
            continue
    return out


def fetch_nonsession_ranges(year: int) -> list[tuple[dt.date, dt.date]]:
    r = httpx.get(SCHEDULE_XML_URL.format(year=year), timeout=30, headers=HEADERS, follow_redirects=True)
    r.raise_for_status()
    return parse_nonsession_ranges(r.content)


def expected_session_days(today: dt.date, deadline: dt.date, blackouts: list[tuple[dt.date, dt.date]]) -> int:
    """Weekdays in [today, deadline) outside announced non-legislative periods.

    A tentative-schedule estimate (upper bound): the Senate can adjourn early
    or convene pro forma. An urgency gauge, not a precision instrument.
    """
    n = 0
    d = today
    while d < deadline:
        if d.weekday() < 5 and not any(b <= d <= e for b, e in blackouts):
            n += 1
        d += dt.timedelta(days=1)
    return n


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

    today = dt.date.today()
    deadlines = {c["ticker"]: today + dt.timedelta(days=int(c["days_to_close"])) for c in targets}
    blackouts: list[tuple[dt.date, dt.date]] = []
    schedule_ok = True
    for year in range(today.year, max(deadlines.values()).year + 1):
        try:
            blackouts += fetch_nonsession_ranges(year)
        except Exception as e:
            # next year's schedule may simply not be announced yet; without the
            # current year's, though, the count would be meaningless
            if year == today.year:
                schedule_ok = False
                print(f"watcher: {year} schedule fetch failed ({e}); session days unknown")

    lines = [f"# Tail signals — {today}", ""]
    records = []
    checked = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for c in targets:
        nominee = extract_nominee(c["title"])
        sig, ev = assess(nominee, cal_text)
        c["tail_signal"] = sig
        nsess = expected_session_days(today, deadlines[c["ticker"]], blackouts) if schedule_ok else None
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
            f"(~{nsess if nsess is not None else '?'} expected session days before deadline)\n"
            f"  - {ev}"
        )
    CANDIDATES.write_text(json.dumps(cands))
    TAIL_SIGNALS.write_text(json.dumps(records, indent=1))
    feature_rows = []
    checked_dt = dt.datetime.fromisoformat(checked)
    for record in records:
        feature_rows.append(
            {
                "source": "senate-executive-calendar",
                "entity": record["ticker"],
                "metric": "confirmation_tail_signal",
                "effective_at": checked_dt,
                "available_at": checked_dt,
                "retrieved_at": checked_dt,
                "value": record["signal"],
                "revision": today.isoformat(),
                "evidence": record["evidence"],
            }
        )
    feature_path = FEATURES / f"senate-executive-calendar-{today:%Y%m%d}.parquet"
    write_partition(normalize_features(pl.DataFrame(feature_rows)), feature_path)
    (REPORTS / "tail_signals.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    run()
