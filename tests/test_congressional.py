import datetime as dt

from kalshi_data.watchers.congressional import (
    extract_nominee,
    last_name,
    session_days_before,
    signal,
)


def test_extract_nominee_handles_nicknames_and_plain_names():
    assert extract_nominee('Will Walter "Jay" Clayton be confirmed as U.S. Attorney') == "Walter Clayton"
    assert extract_nominee("Will Casey Means be confirmed as Surgeon General before Aug") == "Casey Means"
    assert extract_nominee("Will the 7-day moving average of transit calls...") is None


def test_signal_clear_when_absent_from_calendar():
    assert signal("Casey Means", "calendar text with other names only") == "CLEAR"


def test_signal_warm_when_on_calendar():
    assert signal("Casey Means", "NOMINATIONS ... Casey Means, to be Surgeon General") == "WARM"


def test_signal_hot_when_in_cloture_section():
    text = "NOMINATIONS ... other people ... CLOTURE MOTIONS ... motion on Means nomination"
    assert signal("Casey Means", text) == "HOT"


def test_signal_unknown_on_missing_inputs():
    assert signal(None, "text") == "UNKNOWN"
    assert signal("Casey Means", "") == "UNKNOWN"


def test_session_days_counts_only_days_before_deadline():
    today = dt.date.today()
    days = [today + dt.timedelta(days=i) for i in (1, 3, 5, 30)]
    assert session_days_before(today + dt.timedelta(days=10), days) == 3


def test_session_days_none_when_feed_has_only_past_days():
    today = dt.date.today()
    past = [today - dt.timedelta(days=i) for i in (10, 5, 2)]
    assert session_days_before(today + dt.timedelta(days=10), past) is None


def test_last_name():
    assert last_name("Walter Clayton") == "Clayton"
