import httpx

from kalshi_data.core.client import KalshiClient


def _client_with(handler):
    return KalshiClient(rps=10_000, transport=httpx.MockTransport(handler))


def test_paginate_follows_cursor_to_exhaustion():
    pages = {
        None: {"markets": [{"ticker": "A"}], "cursor": "c1"},
        "c1": {"markets": [{"ticker": "B"}], "cursor": "c2"},
        "c2": {"markets": [], "cursor": ""},
    }

    def handler(request):
        cursor = dict(request.url.params).get("cursor")
        return httpx.Response(200, json=pages[cursor])

    client = _client_with(handler)
    items = [m for page in client.paginate("/markets", "markets") for m in page]
    assert [m["ticker"] for m in items] == ["A", "B"]


def test_get_retries_on_429_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429)
        return httpx.Response(200, json={"ok": True})

    client = _client_with(handler)
    assert client.get("/series") == {"ok": True}
    assert calls["n"] == 3


def test_get_drops_none_params():
    def handler(request):
        assert "cursor" not in dict(request.url.params)
        return httpx.Response(200, json={})

    _client_with(handler).get("/markets", cursor=None, limit=5)
