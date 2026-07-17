import datetime as dt

from kalshi_data.watchers.congressional import (
    expected_session_days,
    extract_nominee,
    last_name,
    parse_nonsession_ranges,
    signal,
)


def test_extract_nominee_handles_nicknames_and_plain_names():
    assert extract_nominee('Will Walter "Jay" Clayton be confirmed as U.S. Attorney') == "Walter Clayton"
    assert extract_nominee("Will Casey Means be confirmed as Surgeon General before Aug") == "Casey Means"
    assert extract_nominee("Will the 7-day moving average of transit calls...") is None


def test_last_name_skips_generational_suffixes():
    assert last_name("Walter Clayton") == "Clayton"
    assert last_name("Preston Wells Griffith III") == "Griffith"
    assert last_name("Martin Luther King Jr.") == "King"


def test_signal_clear_when_absent_from_calendar():
    assert signal("Casey Means", "calendar text with other names only") == "CLEAR"


def test_signal_warm_needs_full_name_not_just_surname():
    assert signal("Casey Means", "NOMINATIONS ... Casey Means, to be Surgeon General") == "WARM"
    # middle initials between first and last name still match
    assert signal("Casey Means", "NOMINATIONS ... Casey R. Means, of Tennessee, to be") == "WARM"


def test_signal_clear_on_predecessor_vice_clause():
    # the live false positive of 2026-07-17: 'Clayton' was the *predecessor's*
    # first name in a Marshal nomination, not our nominee
    text = (
        "Jane Holt, of Oklahoma, to be United States Marshal for the term of "
        "four years, vice Clayton D. Johnson, term expired. Reported by Mr. Grassley"
    )
    assert signal("Walter Clayton", text) == "CLEAR"
    # a surname later in the vice clause is also a predecessor reference
    assert signal("Roberta Johnson", text) == "CLEAR"


def test_signal_clear_on_senator_honorific_mention():
    text = "May 18, 2026 Reported by Mr. Grassley, Committee on the Judiciary"
    assert signal("Charles Grassley", text) == "CLEAR"


def test_signal_unknown_on_unexplained_surname_mention():
    # surname present, first name absent, no mechanical explanation -> needs eyes
    assert signal("Walter Clayton", "the Clayton nomination is pending") == "UNKNOWN"


def test_signal_hot_full_name_on_calendar_and_surname_in_cloture():
    text = (
        "NOMINATIONS Casey Means, of Tennessee, to be Surgeon General "
        "... CLOTURE ... motion on the Means nomination"
    )
    assert signal("Casey Means", text) == "HOT"


def test_signal_warm_when_cloture_section_names_someone_else():
    text = (
        "NOMINATIONS Casey Means, of Tennessee, to be Surgeon General "
        "... CLOTURE ... motion on the Flowers nomination"
    )
    assert signal("Casey Means", text) == "WARM"


def test_signal_single_token_name_falls_back_to_surname_match():
    assert signal("Bessent", "NOMINATIONS ... Scott Bessent, to be Secretary") == "WARM"


def test_signal_unknown_on_missing_inputs():
    assert signal(None, "text") == "UNKNOWN"
    assert signal("Casey Means", "") == "UNKNOWN"


def test_parse_nonsession_ranges():
    xml = b"""<?xml version="1.0"?><schedule><dates>
      <date><beginDate>2026-08-10</beginDate><endDate>2026-09-11</endDate>
        <action>State Work Period</action></date>
      <date><beginDate>2026-09-21</beginDate><endDate>2026-09-21</endDate></date>
    </dates></schedule>"""
    assert parse_nonsession_ranges(xml) == [
        (dt.date(2026, 8, 10), dt.date(2026, 9, 11)),
        (dt.date(2026, 9, 21), dt.date(2026, 9, 21)),
    ]


def test_expected_session_days_counts_weekdays_outside_blackouts():
    # Mon 2026-07-20 .. Fri 2026-07-31 exclusive: 9 weekdays in [20, 31)
    today = dt.date(2026, 7, 20)
    deadline = dt.date(2026, 7, 31)
    assert expected_session_days(today, deadline, []) == 9
    # blackout swallowing the first week leaves Mon-Thu of the second
    blackout = [(dt.date(2026, 7, 20), dt.date(2026, 7, 24))]
    assert expected_session_days(today, deadline, blackout) == 4


def test_expected_session_days_deadline_exclusive_and_weekend_free():
    # Sat -> Mon deadline: zero weekdays in between
    assert expected_session_days(dt.date(2026, 7, 18), dt.date(2026, 7, 20), []) == 0
