import datetime as dt

from kalshi_data.ingest.recorder import near_close


NOW = dt.datetime(2026, 7, 18, 12, 0, tzinfo=dt.timezone.utc)


def _iso(hours: float) -> str:
    return (NOW + dt.timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def test_near_close_keeps_only_markets_inside_the_window():
    markets = {
        "IN-6H": _iso(6),
        "IN-35H": _iso(35),
        "OUT-40H": _iso(40),
        "ALREADY-CLOSED": _iso(-1),
        "NO-CLOSE-TIME": None,
        "BAD-FORMAT": "not-a-date",
    }
    assert near_close(markets, 36, now=NOW) == ["IN-6H", "IN-35H"]


def test_near_close_boundary_is_inclusive_at_horizon_exclusive_at_now():
    markets = {"AT-HORIZON": _iso(36), "AT-NOW": _iso(0)}
    assert near_close(markets, 36, now=NOW) == ["AT-HORIZON"]
