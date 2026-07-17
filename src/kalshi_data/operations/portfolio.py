"""Real-portfolio sync: balance, positions, resting orders, settlements.

Read-only (see core/auth_client.py). Writes data/state/portfolio.json for the
dashboard. On first successful sync, records the account equity as the return
baseline in data/state/portfolio_baseline.json - all returns measure from there.
Degrades gracefully when no credentials are present.
"""

from __future__ import annotations

import datetime as dt
import json

from ..core import auth_client
from ..core.paths import STATE

PORTFOLIO = STATE / "portfolio.json"
BASELINE = STATE / "portfolio_baseline.json"


def _cents(v) -> float:
    return float(v or 0) / 100


def run() -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    if not auth_client.credentials_present():
        PORTFOLIO.write_text(json.dumps({
            "available": False, "ts": now,
            "reason": "no API credentials at ~/.kalshi/ (see README: real portfolio setup)",
        }))
        print("portfolio: no credentials, wrote unavailable stub")
        return

    c = auth_client.KalshiAuthedClient()
    balance = c.get("/portfolio/balance")
    positions = c.get("/portfolio/positions").get("market_positions", []) or []
    orders = c.get("/portfolio/orders", status="resting").get("orders", []) or []
    settlements = c.get("/portfolio/settlements", limit=200).get("settlements", []) or []

    cash = _cents(balance.get("balance"))
    pos_rows = []
    exposure = 0.0
    for p in positions:
        qty = p.get("position", 0)
        if not qty:
            continue
        value = _cents(p.get("market_exposure"))
        exposure += abs(value)
        pos_rows.append({
            "ticker": p.get("ticker"),
            "position": qty,
            "side": "YES" if qty > 0 else "NO",
            "exposure_usd": round(abs(value), 2),
            "realized_usd": round(_cents(p.get("realized_pnl")), 2),
            "fees_usd": round(_cents(p.get("fees_paid")), 2),
        })
    from ..core.parse import cents, quantity

    order_rows = [{
        "ticker": o.get("ticker"),
        "side": o.get("side"),
        "price_c": cents(o, "no_price") if o.get("side") == "no" else cents(o, "yes_price"),
        "resting": quantity(o, "remaining_count") or 0,
    } for o in orders]

    equity = round(cash + exposure, 2)
    if not BASELINE.exists():
        BASELINE.write_text(json.dumps({"baseline_usd": equity, "since": now}))
    base = json.loads(BASELINE.read_text())
    pnl = round(equity - base["baseline_usd"], 2)
    days = max((dt.datetime.fromisoformat(now) - dt.datetime.fromisoformat(base["since"])).days, 0)

    settled_rows = [{
        "ticker": s.get("ticker"),
        "revenue_usd": round(_cents(s.get("revenue")), 2),
        "settled": (s.get("settled_time") or "")[:10],
    } for s in settlements[:20]]

    unit = round(0.025 * equity, 2)
    out = {
        "available": True, "ts": now,
        "cash_usd": round(cash, 2), "exposure_usd": round(exposure, 2), "equity_usd": equity,
        "baseline_usd": base["baseline_usd"], "since": base["since"][:10],
        "pnl_usd": pnl, "days": days,
        "sizing": {"politics_unit_usd": unit, "financials_unit_usd": round(unit / 2, 2)},
        "positions": pos_rows, "resting_orders": order_rows, "recent_settlements": settled_rows,
    }
    PORTFOLIO.write_text(json.dumps(out, indent=1))
    print(f"portfolio: equity ${equity:,.2f} (cash ${cash:,.2f} + exposure ${exposure:,.2f}), "
          f"P&L ${pnl:+,.2f} over {days}d, {len(pos_rows)} positions, {len(order_rows)} resting")


if __name__ == "__main__":
    run()
