"""Defensive field extraction: the API mixes integer-cent, float-string-dollar,
and fixed-point-string forms of the same quantity depending on market vintage."""

from __future__ import annotations


def cents(m: dict, base: str) -> int | None:
    """Price-like field in integer cents, whichever form the API sent."""
    v = m.get(base)
    if v is not None:
        return int(v)
    d = m.get(f"{base}_dollars")
    if d is not None:
        return round(float(d) * 100)
    return None


def quantity(m: dict, base: str) -> float | None:
    """Size-like field (volume, open interest, liquidity) as a float."""
    for key in (base, f"{base}_fp", f"{base}_dollars"):
        v = m.get(key)
        if v is not None:
            return float(v)
    return None


def market_row(m: dict, series_meta: dict) -> dict:
    return {
        "ticker": m.get("ticker"),
        "event_ticker": m.get("event_ticker"),
        "series_ticker": series_meta.get("ticker"),
        "category": series_meta.get("category"),
        "tier": series_meta.get("tier"),
        "frequency": series_meta.get("frequency"),
        "fee_type": series_meta.get("fee_type"),
        "fee_multiplier": series_meta.get("fee_multiplier"),
        "market_type": m.get("market_type"),
        "status": m.get("status"),
        "result": m.get("result"),
        "can_close_early": m.get("can_close_early"),
        "open_time": m.get("open_time"),
        "close_time": m.get("close_time"),
        "expiration_time": m.get("expiration_time") or m.get("latest_expiration_time"),
        "expected_expiration_time": m.get("expected_expiration_time"),
        # Current API calls this settlement_ts; older payloads/tests used
        # settled_time. Preserve one canonical field in our store.
        "settled_time": m.get("settlement_ts") or m.get("settled_time"),
        "last_price_cents": cents(m, "last_price"),
        "volume": quantity(m, "volume"),
        "open_interest": quantity(m, "open_interest"),
        "liquidity": quantity(m, "liquidity"),
    }
